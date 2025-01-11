import os
import asyncio
import tempfile
import sounddevice as sd
import numpy as np

from scipy.io.wavfile import write
from rich.console import Console

from superagentx.agentxpipe import AgentXPipe
from superagentx.llm.openai import OpenAI


# Parameters for recording
sample_rate = 44100  # Hz
channels = 1
dtype = 'int16'


class WhisperPipe:
    def __init__(
            self,
            *,
            search_name: str,
            agentx_pipe: AgentXPipe,
            read_prompt: str | None = None,
            write_prompt: str | None = None
    ):
        """
        Initializes the WhisperPipe with necessary parameters for configuring an agentxpipe that interacts with a specified
        search mechanism and handles websocket connections.

        Args:
            search_name: The name of the search mechanism or service that the WhisperPipe will utilize. This name is used
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

        # Retrieve the API key from the environment variable
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Set 'OPENAI_API_KEY'.")

        self.client = OpenAI(api_key=self.api_key)
        self.agentx_pipe = agentx_pipe
        self._read_prompt = read_prompt or ''
        self._write_prompt = write_prompt or ''
        self.is_recording = True
        self.transcription = None
        self._console = Console()

    async def stop_recording(self):
        """Stop recording when 'Enter' key is pressed."""
        self._console.print("Press [bold yellow]Enter[/bold yellow] to stop recording.")
        await asyncio.get_event_loop().run_in_executor(None, input)
        self.is_recording = False

    async def record_audio(self):
        """Record audio until 'Enter' is pressed."""
        self._console.print("Recording...")

        audio_frames = []

        def audio_callback(indata, frames, time, status):
            if status:
                self._console.print(f"Status: {status}")
            if self.is_recording:
                audio_frames.append(indata.copy())

        # Start recording
        with sd.InputStream(samplerate=sample_rate, channels=channels, dtype=dtype, callback=audio_callback):
            while self.is_recording:
                await asyncio.sleep(0.1)

        # Combine recorded audio frames
        recorded_audio = np.concatenate(audio_frames, axis=0)

        # Save to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            write(temp_audio_file.name, sample_rate, recorded_audio)
            self._console.print(f"Audio saved to {temp_audio_file.name}")
            return temp_audio_file.name

    async def transcribe_audio(self, file_path):
        """Transcribe the recorded audio using OpenAI Whisper."""
        self._console.print("[bold yellow]Transcribing audio...[/bold yellow]")
        with open(file_path, "rb") as audio_file:
            # Run the synchronous transcription method in an asynchronous context
            transcription = await asyncio.to_thread(
                self.client.audio.transcriptions.create,
                model="whisper-1",
                file=audio_file
            )
        return transcription.text

    async def start(self):
        """Start the recording and transcription process."""
        # Start `stop_recording` and `record_audio` concurrently
        stop_task = asyncio.create_task(self.stop_recording())
        record_task = asyncio.create_task(self.record_audio())

        with self._console.status("[bold yellow]Ask your query...\n", spinner="aesthetic"):
            await asyncio.wait([stop_task, record_task], return_when=asyncio.FIRST_COMPLETED)

        # Get the recorded file path
        audio_file_path = await record_task

        with self._console.status("[bold yellow]Transcribing audio...\n", spinner="aesthetic"):
            query = await self.transcribe_audio(audio_file_path)

            # Ensure `agentx_pipe` is initialized
            if not self.agentx_pipe:
                raise ValueError("AgentXPipe is not initialized.")

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

        self._console.print(f"Transcription: [bold yellow]{query}[/bold yellow]")
