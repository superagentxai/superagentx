import whisper
import asyncio
import tempfile
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from rich.console import Console

from superagentx.agentxpipe import AgentXPipe

# Parameters for recording
SAMPLE_RATE = 44100  # Hz
CHANNELS = 1
DTYPE = 'int16'
RECORD_DURATION = 10


class WhisperPipe:
    def __init__(
            self,
            *,
            search_name: str,
            agentx_pipe: AgentXPipe,
            read_prompt: str | None = None,
            write_prompt: str | None = None
    ):
        # Load the Whisper model
        self.model = whisper.load_model("base")  # Use "tiny", "small", "medium", or "large" as needed
        self.agentx_pipe = agentx_pipe
        self._read_prompt = read_prompt or ''
        self._write_prompt = write_prompt or ''
        self.transcription = None
        self._console = Console()

    async def record_audio(self):
        """Record audio for a fixed duration."""
        # Display the status message while recording
        with self._console.status("[bold yellow]Ask your query...[/bold yellow]"):
            audio_frames = []

            def audio_callback(indata, frames, time, status):
                if status:
                    self._console.print(f"Status: {status}")
                audio_frames.append(indata.copy())

            # Start recording
            with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    callback=audio_callback
            ):
                await asyncio.sleep(RECORD_DURATION)

        # Combine recorded audio frames
        recorded_audio = np.concatenate(audio_frames, axis=0)

        # Save to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            write(temp_audio_file.name, SAMPLE_RATE, recorded_audio)
            return temp_audio_file.name

    async def transcribe_audio(self, file_path):
        """Transcribe the recorded audio using Whisper."""
        self._console.print("[bold yellow]Transcribing audio...[/bold yellow]")

        # Run Whisper transcription
        result = self.model.transcribe(file_path)

        # Check the transcription result
        if "text" in result and result["text"].strip():
            self._console.print(f"[bold green]Transcription successful:[/bold green] {result['text']}")
            return result["text"]
        else:
            self._console.print("[bold red]Transcription failed or resulted in empty text.[/bold red]")
            return ""

    async def start(self):
        """Start the recording and transcription process."""
        # Record the audio
        audio_file_path = await self.record_audio()

        # Transcribe the audio with the bouncing ball spinner
        with self._console.status("[bold yellow]Transcribing audio...\n", spinner="bouncingBall"):
            query = await self.transcribe_audio(audio_file_path)

            # Ensure agentx_pipe is initialized
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

        # Print the transcribed text
        self._console.print(f"Transcription: [bold yellow]{query}[/bold yellow]")

