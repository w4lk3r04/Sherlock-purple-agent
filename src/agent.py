from dotenv import load_dotenv
import litellm

from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger

load_dotenv()


class Agent:
    def __init__(self):
        self.messenger = Messenger()
        # Initialize conversation history for multi-turn interactions
        self.messages = []

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Sherlock Purple Agent - Cybersecurity Exploit Generation.

        Args:
            message: The incoming message containing vulnerability description or task
            updater: Report progress (update_status) and results (add_artifact)

        This agent analyzes vulnerability descriptions and generates proof-of-concept
        exploits using format-aware PoC generation and crash-output-driven mutation.
        """
        input_text = get_message_text(message)
        print(f"> User: {input_text}")

        await updater.update_status(
            TaskState.working, new_agent_text_message("Analyzing vulnerability and generating exploit...")
        )

        # Build the conversation context with system prompt
        if not self.messages:
            system_prompt = """You are Sherlock, an autonomous cybersecurity agent specialized in exploit generation.
Your capabilities include:
1. Format-aware PoC generation: Identify expected binary input formats before crafting exploits
2. Crash-output-driven mutation: Iteratively refine PoCs based on sanitizer feedback
3. Deliberate zero-day discovery: Pivot to open-ended vulnerability hunting when reproduction fails
4. Best-of-N sampling: Maximize success rate across multiple attempts

When given a vulnerability description and codebase information, generate detailed proof-of-concept exploits
that can reproduce the vulnerability. Provide clear explanations of the exploit mechanism and expected outcomes."""
            
            self.messages.append({"content": system_prompt, "role": "system"})

        # Add user message to conversation history
        self.messages.append({"content": input_text, "role": "user"})

        # Generate response using OpenAI via litellm
        try:
            completion = litellm.completion(
                model="gpt-4o",
                messages=self.messages
            )
            response = completion.choices[0].message.content
            
            # Add assistant response to conversation history
            self.messages.append({"content": response, "role": "assistant"})
            print(f"< Sherlock: {response}")

            # Return the exploit/analysis as an artifact
            await updater.add_artifact(
                parts=[Part(root=TextPart(text=response))],
                name="Exploit Analysis",
            )
        except Exception as e:
            error_msg = f"Error generating exploit: {str(e)}"
            print(f"< Error: {error_msg}")
            await updater.add_artifact(
                parts=[Part(root=TextPart(text=error_msg))],
                name="Error",
            )
