import logging
import random
import re
import sys
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

from superagentx.computer_use.browser.models import StepInfo, ToolResult
from superagentx.computer_use.browser.state import BrowserState
from superagentx.computer_use.browser.models import ToastConfig

# Define generic type variables for return type and parameters
R = TypeVar('R')
P = ParamSpec('P')

logger = logging.getLogger(__name__)


async def get_user_message(
        state: BrowserState,
        step_info: StepInfo,
        action_result: list[ToolResult],
        use_vision: bool = True
):
    include_attributes = [
        'title',
        'type',
        'name',
        'role',
        'aria-label',
        'placeholder',
        'value',
        'alt',
        'aria-expanded',
        'data-date-format'
    ]

    elements_text = state.element_tree.clickable_elements_to_string(
        include_attributes=include_attributes
    )

    has_content_above = (state.pixels_above or 0) > 0
    has_content_below = (state.pixels_below or 0) > 0

    elem_text = elements_text

    if elements_text:
        if has_content_above:
            elements_text = (
                f'... {state.pixels_above} pixels above - scroll or extract content to see more ...\n{elements_text}'
            )
        else:
            elements_text = f'[Start of page]\n{elements_text}'
        if has_content_below:
            elements_text = (
                f'{elements_text}\n... {state.pixels_below} pixels below - scroll or extract content to see more ...'
            )
        else:
            elements_text = f'{elements_text}\n[End of page]'
    else:
        elements_text = 'empty page'

    if step_info:
        step_info_description = f'Current step: {step_info.step_number + 1}/{step_info.max_steps}'
    else:
        step_info_description = ''
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    step_info_description += f'Current date and time: {time_str}'

    state_description = f"""
[Task history memory ends]
[Current state starts here]
The following is one-time information - if you need to remember it write it to memory:
Current url: {state.url}
Available tabs:
{state.tabs}
Interactive elements from top layer of the current page inside the viewport:
{elements_text}
{step_info_description}
"""

    if action_result:
        for i, result in enumerate(action_result):
            if result.extracted_content:
                state_description += f'\nAction result {i + 1}/{len(action_result)}: {result.extracted_content}'
            if result.error:
                # only use last line of error
                error = result.error.split('\n')[-1]
                state_description += f'\nAction error {i + 1}/{len(action_result)}: ...{error}'

    if state.screenshot and use_vision:
        msg = {
            "role": "user",
            "content": [{
                "type": "text",
                "text": state_description
            }, {
                'type': 'image_url',
                'image_url': {'url': f'data:image/png;base64,{state.screenshot}'},  # , 'detail': 'low'
            }
            ]
        }
        return {
            "msg": msg,
            "element_text": elem_text
        }
    msg = {
        "role": "user",
        "content": state_description
    }
    return {
        "msg": msg,
        "element_text": elem_text
    }


async def log_response(result: dict):
    if 'Success' in result.get('current_state').get('evaluation_previous_goal'):
        emoji = '👍'
    elif 'Failed' in result.get('current_state').get('evaluation_previous_goal'):
        emoji = '⚠'
    else:
        emoji = '🤷'

    logger.info(f"{emoji} Eval: {result.get('current_state').get('evaluation_previous_goal')}")
    logger.info(f"Memory: {result.get('current_state').get('memory')}")
    logger.info(f"Next goal: {result.get('current_state').get('next_goal')}")
    logger.info(f"Action {result.get('action')}")


async def show_toast(
        page: Any,
        message: str,
        duration: int = 3000,
        toast_config: ToastConfig | None = None
):
    if not toast_config:
        toast_config = ToastConfig()
    import playwright._impl._errors

    icons = ['🚀', '🔥', '💡', '⭐']
    random_icon = random.choice(icons)
    if message:
        message = message.replace('\n', ' ')
        message = re.sub(r"[^\w\s.,:+()₹/]", "", message)
        final_message = f"SuperAgentX Goal: {random_icon} {message}"
    else:
        final_message = ''

    font_size = toast_config.font_size
    toast_script = f"""
    (() => {{
        const message = `{final_message}`;
        let toast = document.createElement('div');
        toast.innerText = message;

        const screenWidth = window.innerWidth;
        const fontSize = screenWidth > 1920 ? '{font_size}px' : screenWidth > 1280 ? '{font_size - 2}px' : '{font_size - 4}px';
        const padding = screenWidth > 1920 ? '20px 30px' : screenWidth > 1280 ? '18px 26px' : '16px 24px';

        toast.style.position = 'fixed';
        toast.style.top = '40px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.background = '{toast_config.background}';
        toast.style.color = '{toast_config.color}';
        toast.style.padding = padding;
        toast.style.borderRadius = '16px';
        toast.style.fontSize = fontSize;
        toast.style.zIndex = 9999;
        toast.style.boxShadow = '0 8px 20px rgba(0,0,0,0.3)';
        toast.style.transition = 'opacity 0.3s ease';
        toast.style.opacity = '1';

        document.body.appendChild(toast);

        setTimeout(() => {{
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }}, {duration});
    }})();
    """

    try:
        await page.evaluate(toast_script)
    except playwright._impl._errors.Error as ex:
        logger.error(f"Toast Error: {ex}")
        await page.evaluate(toast_script.format(final_message="Doing Next step....", duration=duration))


def manipulate_string(string: str):
    start = '```json\n'
    end = '```'
    if start in string:
        r = re.findall(re.escape(start) + "(.+?)" + re.escape(end), string, re.DOTALL)
        if r:
            return r[0]
        else:
            return string
    return string


def time_execution_sync(additional_text: str = '') -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f'{additional_text} Execution time: {execution_time:.2f} seconds')
            return result

        return wrapper

    return decorator


def time_execution_async(
        additional_text: str = '',
) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
    def decorator(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f'{additional_text} Execution time: {execution_time:.2f} seconds')
            return result

        return wrapper

    return decorator


BROWSER_SYSTEM_MESSAGE = """

You are an AI agent designed to automate browser tasks. Your goal is to accomplish the ultimate task by following the rules carefully and efficiently.

# Input Format

Task

Previous steps

Current URL

Open Tabs

Interactive Elements

[index]<type>text</type>

- index: Numeric identifier for interaction

- type: HTML element type (button, input, etc.)

- text: Element description

Example:

[33]<button>Submit Form</button>

- Only elements with numeric indexes in [] are interactive.

- Elements without [] provide context only.

# Response Rules

1. RESPONSE FORMAT:

You must ALWAYS respond with valid JSON in this exact structure:

{

  "current_state": {

    "evaluation_previous_goal": "Success|Failed|Unknown - Analyze the current elements and the image to check if the previous goals/actions are successful as intended by the task. Mention if something unexpected happened. Briefly state why/why not.",

    "memory": "Description of what has been done and what must be remembered. Be very specific. Always count progress (e.g., 0 out of 10 websites analyzed). Mention the next subgoal clearly.",

    "next_goal": "Describe the next immediate step or goal to move forward."

  },

  "action": [

    {"one_action_name": { /* action-specific parameters */ }},

    // ... more actions in sequence (up to {{max_actions}})

  ]

}

2. ACTIONS:

- Use a maximum of {{max_actions}} actions per response.

- Specify only one action name per object in the action list.

- Form filling example:

[

  {"input_text": {"index": 1, "text": "username"}},

  {"input_text": {"index": 2, "text": "password"}},

  {"click_element_by_index": {"index": 3}}

]

- If page state changes after an action, the sequence is interrupted and a new state will be returned.

- Be efficient: fill entire forms before clicking submit, chain actions only where it makes sense.

3. ELEMENT INTERACTION:

- Use only indexes from the provided interactive elements.

- Non-interactive texts are for context only.

4. NAVIGATION & ERROR HANDLING:

- If no suitable elements exist, switch strategy using available actions.

- If stuck, try alternatives: go back, new search, open new tab, etc.

- Handle cookie banners and popups by accepting or closing them.

- Use scroll actions to reveal hidden elements if necessary.

- If a captcha appears, attempt to solve; if unsolvable, try alternative paths.

- Use `wait` to pause if necessary, but do not overuse. Follow the login wait rule below.

5. LOGIN ACTION:

*WAIT FOR USER MANUAL LOGIN*

- If the task or flow involves a user login (manual or automated) and after triggering the login form submission the 
system detects that human action is required:

    - Use `wait` actions with a maximum total wait time of 5 minutes.

    - Always break the wait into intervals (e.g., 60 seconds) and check for page state changes between intervals.
    
    - If need Authenticator, wait 20 seconds

    - Example:

[

  {"wait": {"duration": 60}}

]

- Repeat this pattern until the login completes or the total of 5 minutes has elapsed.

- After 5 minutes, if login has not been completed, mark `evaluation_previous_goal` as `Failed` and record this in `memory`.

6. TASK COMPLETION:

- Use the `done` action only when the ultimate task is complete or the maximum allowed steps are reached.

- When using `done`, include all gathered information in the `text` field.

- If the full task is complete, set `success: true` in `done`. If not fully complete, set `success: false` but still provide the partial results.

7. LONG TASKS:

- Use `memory` to track repetitive tasks and loop counts.

- If the task involves iterating over a list, always track progress clearly (e.g., 3 out of 7 profiles checked).

8. EXTRACTION:

- When asked to retrieve information, use `extract_content` and store the results.

- Do not skip extraction steps even if information seems visible; always call the correct action.

9. VISUAL CONTEXT:

- If provided, use images and bounding boxes to interpret page layout.

- Bounding box labels indicate the corresponding element index.

Your responses must always conform to this JSON structure, with strict adherence to these rules.

"""

COT_BROWSER_SYSTEM_MESSAGE = (
    "### Thought Process for Browser Automation AI Agent\n\n"
    "1. **Understand the Task**\n"
    "- Extract the ultimate goal from the input.\n"
    "- Identify any constraints, conditions, or specific requirements.\n"
    "- Break down complex tasks into sub-tasks.\n\n"

    "2. **Analyze the Current Context**\n"
    "- Check the current URL to determine if the correct page is loaded.\n"
    "- Review the available interactive elements (buttons, inputs, links).\n"
    "- Identify any pre-filled or auto-populated fields.\n"
    "- Evaluate previous steps and their success/failure states.\n\n"

    "3. **Evaluate Navigation Requirements**\n"
    "- If the required page is not loaded, determine if navigation is necessary.\n"
    "- Decide if a search needs to be performed to find relevant content.\n"
    "- Open a new tab if additional research is required.\n\n"

    "4. **Determine the Optimal Action Sequence**\n"
    "- Identify minimal steps to achieve the goal efficiently.\n"
    "- Group actions that can be executed together without interruptions.\n"
    "- Prioritize filling forms in bulk before submitting.\n"
    "- Identify dependencies (e.g., clicking a dropdown before selecting an option).\n\n"

    "5. **Handle Interactive Elements**\n"
    "- Locate necessary buttons, forms, and links based on their indexes.\n"
    "- Scroll if elements are not visible.\n"
    "- Click, input text, or extract content as required.\n"
    "- Handle dynamic elements that appear after interactions (e.g., modal popups).\n\n"

    "6. **Address Potential Errors and Unexpected Situations**\n"
    "- If an element is missing, attempt to reload the page or navigate differently.\n"
    "- Handle popups, cookies, or captchas automatically.\n"
    "- Use wait actions if the page is loading slowly.\n"
    "- If stuck, explore alternative approaches (e.g., searching again, trying another tab).\n\n"

    "7. **Track Memory and Progress**\n"
    "- Maintain a counter for repeated tasks (e.g., processing multiple items).\n"
    "- Store key details about the process (e.g., already filled fields, visited links).\n"
    "- Continuously evaluate if the goal is being met.\n\n"

    "8. **Ensure Proper Extraction and Storage**\n"
    "- If information needs to be gathered, use extraction methods effectively.\n"
    "- Save relevant data in memory for further processing.\n"
    "- If required, extract and return structured data.\n\n"

    "9. **Decide When the Task is Completed**\n"
    "- If all required actions are successfully executed, mark the task as done.\n"
    "- Ensure all requested information is included in the final response.\n"
    "- If max steps are reached without full completion, provide partial results.\n"
    "- Do not hallucinate success—verify the task outcome before marking completion.\n\n"

    "10. **Respond in Structured JSON Format**\n"
    "- Ensure output always follows the predefined JSON schema.\n"
    "- Include evaluation of previous steps, current memory status, and next goals.\n"
    "- Structure actions sequentially with clear dependencies.\n"
)
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

SYSTEM_MESSAGE = [
    {
        "role": "system",
        "content": f"{BROWSER_SYSTEM_MESSAGE}\n\nNote:\nEnsure to first build the step by step "
                   f"process, once you build the steps then execute the steps use click event "
                   f"for every step to need. Don't give the duplicate json."
    }
]


def get_screen_resolution():
    if sys.platform == 'darwin':  # macOS
        try:
            from AppKit import NSScreen

            screen = NSScreen.mainScreen().frame()
            return {'width': int(screen.size.width), 'height': int(screen.size.height)}
        except ImportError:
            print('AppKit is not available. Make sure you are running this on macOS with pyobjc installed.')
        except Exception as e:
            print(f'Error retrieving macOS screen resolution: {e}')
        return {'width': 2560, 'height': 1664}

    else:  # Windows & Linux
        try:
            from screeninfo import get_monitors

            monitors = get_monitors()
            if not monitors:
                raise Exception('No monitors detected.')
            monitor = monitors[0]
            return {'width': monitor.width, 'height': monitor.height}
        except ImportError:
            print("screeninfo package not found. Install it using 'pip install screeninfo'.")
        except Exception as e:
            print(f'Error retrieving screen resolution: {e}')

        return {'width': 1920, 'height': 1080}


def get_window_adjustments():
    """Returns recommended x, y offsets for window positioning"""
    if sys.platform == 'darwin':  # macOS
        return -4, 24  # macOS has a small title bar, no border
    elif sys.platform == 'win32':  # Windows
        return -8, 0  # Windows has a border on the left
    else:  # Linux
        return 0, 0
