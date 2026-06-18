from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.llm import LLMClient
from superagentx.llm.models import ChatCompletionParams


class AIHandler(BaseHandler):
    """
        AIHandler is a flexible orchestration class designed to manage a comprehensive
        suite of text-based AI capabilities within the SuperAgentX framework. It provides
        a unified interface for interacting with LLMs and exposes tools that agents can
        call during reasoning, workflows, or autonomous execution.

        This handler can support an extensive range of natural-language and text-processing
        tasks, including but not limited to:

        Core Text Generation
        ---------------------
        - **Freeform Text Generation:** Creative writing, articles, essays, responses,
          instructions, storytelling, dialogue simulation, etc.
        - **Rewriting & Editing:** Grammar correction, paraphrasing, tone adjustments,
          formalization, simplification, expansion, and refinement.
        - **Summarization:** Short, medium, or long summaries of documents, transcripts,
          conversations, PDFs, or datasets.
        - **Translation:** Multi-language translation with domain-specific tuning.

        Analytical & Classification Tasks
        ---------------------------------
        - **Text Classification:** Topic labeling, intent detection, category assignment.
        - **Sentiment Analysis:** Polarity (positive/negative/neutral) and emotion analysis.
        - **Semantic Similarity:** Compare meaning similarity between texts.
        - **Clustering Assistance:** Grouping similar texts via LLM-based reasoning.
        - **Entity Recognition (NER):** Extracting names, dates, locations, organizations.
        - **Information Extraction:** Extracting structured data, attributes, metadata.

        Reasoning & Logic Tasks
        ------------------------
        - **Multi-step Reasoning:** Deep analysis, comparisons, evaluations, breakdowns.
        - **Planning & Strategy:** Action plans, step-by-step solutions, workflow creation.
        - **Deductive/Inductive Reasoning:** Logical problem solving and inference.
        - **Mathematical Reasoning:** Solving equations, word problems, tables (text-based).
        - **Data Interpretation:** Explain charts or numerical tables when provided as text.

        Code & Technical Tasks
        -----------------------
        - **SQL Query Generation:** Convert natural language to SQL.
        - **Code Generation:** Python, JS, Bash, or other languages (small snippets or utilities).
        - **Code Explanation:** Explaining what code does.
        - **Bug Detection (textual):** Identifying issues in code through reasoning.
        - **Regex Generation:** Creating or explaining regular expressions.
        - **API Request Creation:** Generating structured JSON API payloads.

        Knowledge & Retrieval-Style Tasks
        ---------------------------------
        - **Question Answering:** Factual, conceptual, or contextual Q&A.
        - **Knowledge Synthesis:** Combining multiple facts into a coherent explanation.
        - **Document Understanding:** Interpreting and analyzing long text documents.
        - **Pseudo-RAG Reasoning:** Processing user-provided text as a knowledge source.

        Organizational / Productivity Tasks
        -----------------------------------
        - **Note Taking:** Bullet point extraction, key point highlighting.
        - **Task Breakdown:** Turning goals into actionable steps.
        - **Document Drafting:** Proposals, reports, outlines, agendas.
        - **Email & Message Generation:** Professional, casual, or role-specific writing.

    """

    def __init__(
            self,
            llm: LLMClient,
            role: str | None = None,
            story_content: str | None = None
    ):
        super().__init__()
        self.llm = llm
        self.role = role
        self.story_content = story_content

        if not self.role:
            self.role = "You are a helpful assistant."

    @tool
    async def text_creation(
            self,
            *,
            instruction: str
    ):
        """
        Generates or creates some form of text content when called. The text being created might involve combining
        words, sentences, or paragraphs for various purposes. Since it’s part of a larger process, it could be used
        for tasks like preparing data, generating messages, or any other text-related activity.

        Args:
            @param instruction: A string containing the user instruction or prompt that guides the text generation process.

        """
        content = instruction
        if self.story_content:
            content = f"\nBack Story: {self.story_content} Instruction: {instruction}"
        messages = [
            {
                "role": "system",
                "content": self.role
            },
            {
                "role": "user",
                "content": content
            }
        ]
        chat_completion = ChatCompletionParams(
            messages=messages
        )
        return await self.llm.achat_completion(
            chat_completion_params=chat_completion
        )

    async def video_creation(
            self
    ):
        """
            Asynchronously creates or generates video content based on internal logic or preset parameters.
            This method handles the video creation process without requiring external inputs.
        """
        # TODO: Implement later
        pass

    async def image_creation(
            self
    ):
        """
           Asynchronously generates or creates images using predefined settings or internal logic.
           This method manages the image creation process without needing external parameters.
        """
        # TODO: Implement later
        pass
