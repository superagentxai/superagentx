import asyncio
from rich.console import Console
import sounddevice
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.model import TranscriptEvent

from superagentx.agentxpipe import AgentXPipe


class AWSVoicePipe:
    def __init__(
            self,
            *,
            search_name: str,
            agentx_pipe: AgentXPipe,
            read_prompt: str | None = None,
            write_prompt: str | None = None
    ):
        """
        Initializes the VoicePipe with necessary parameters for configuring an agentxpipe that interacts with a specified
        search mechanism and handles websocket connections.

        Args:
            search_name: The name of the search mechanism or service that the VoicePipe will utilize. This name is used
                to identify the search functionality within the broader system.
            agentx_pipe: An instance of AgentXPipe that facilitates communication between the agent, engine and other
                components of the system. This pipe is crucial for data transfer and message handling within the
                agent's operational context.
            read_prompt: An optional prompt string used for guiding the reading information.
                This prompt can help shape the queries made during the search operation. Defaults to None
                if not provided.
            write_prompt: An optional prompt string used for guiding the writing of information.
                This prompt may assist in structuring the responses or data being sent. Defaults to None
                if not provided.
        """
        self.input_stream = None
        self.search_name = search_name
        self.agentx_pipe = agentx_pipe
        self._read_prompt = read_prompt or ''
        self._write_prompt = write_prompt or ''
        self._console = Console()
        self.transcriptions = []

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This method handles transcribed events, accumulating the transcription
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                # Instead of returning, we store the transcriptions in a list
                self.transcriptions.append(alt.transcript)

    @staticmethod
    async def mic_stream(self):
        # This method streams audio from the microphone
        loop = asyncio.get_event_loop()
        input_queue = asyncio.Queue()

        def callback(in_data, frame_count, time_info, _status):
            loop.call_soon_threadsafe(input_queue.put_nowait, (bytes(in_data), _status))

        stream = sounddevice.RawInputStream(
            channels=1,
            samplerate=16000,
            callback=callback,
            blocksize=1024 * 2,
            dtype="int16",
        )
        with stream:
            while True:
                indata, status = await input_queue.get()
                yield indata, status

    async def consume_stream(self, stream, timeout=5):
        # This method consumes the microphone stream and sends audio to Transcribe
        async for chunk, status in self.mic_stream(self):
            if not chunk or len(chunk) == 0:
                print("Received empty chunk, stopping the stream.")
                await stream.input_stream.end_stream()
                break
            await stream.input_stream.send_audio_event(audio_chunk=chunk)

    async def write_chunks(self, stream, timeout=15):
        # This method writes chunks of audio data to the transcription service
        try:
            await asyncio.wait_for(self.consume_stream(stream, timeout), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"No input received within {timeout} seconds, stopping the stream.")
            await self.input_stream.end_stream()

    async def basic_transcribe(self):
        # Main transcription function, connecting to Transcribe service and sending audio
        client = TranscribeStreamingClient(region="us-east-1")
        stream = await client.start_stream_transcription(
            language_code="en-US",
            media_sample_rate_hz=16000,
            media_encoding="pcm"
        )
        self.input_stream = stream.input_stream  # Set the input_stream for later use

        # This will handle transcription events concurrently
        async def handle_transcriptions():
            async for transcript_event in stream.output_stream:
                await self.handle_transcript_event(transcript_event)

        # Run the transcription and event handling concurrently
        with self._console.status("[bold yellow]Ask your query...\n", spinner='aesthetic') as status:
            await asyncio.gather(self.write_chunks(stream), handle_transcriptions())

    def find_best_sentence(self):
        # Sort sentences by length (longer sentences come first)
        print(f"Final transcriptions: {self.transcriptions}")
        sorted_sentences = sorted(
            self.transcriptions,
            key=len,
            reverse=True
        )
        # The first item in the sorted list will be the longest sentence
        return sorted_sentences[0]

    async def start(self) -> None:
        # Start the transcription and print the final transcription results
        await self.basic_transcribe()
        query = self.find_best_sentence()
        self._console.print(f"[bold green]Question Asked : [bold yellow]{query} \n")
        with self._console.status("[bold yellow]Searching...\n", spinner='bouncingBall') as status:
            pipe_result = await self.agentx_pipe.flow(query_instruction=query)
            if pipe_result:
                goal_result = pipe_result[-1]
                if self._write_prompt:
                    self._console.print(self._write_prompt)
                self._console.print(f'\n[bold cyan]Result[/bold cyan]:')
                self._console.print_json(data=goal_result.result)
                self._console.print(f'\n[bold cyan]Reason:[/bold cyan]: {goal_result.reason}\n')
                self._console.print(f'\n[bold cyan]Goal Satisfied[/bold cyan]: {goal_result.is_goal_satisfied}\n')
            else:
                self._console.print("\nNo results found!\n")
        self._console.rule('[bold green]End')

