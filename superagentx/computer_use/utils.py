import random
from datetime import datetime

import base64

from superagentx.constants import BROWSER_SYSTEM_MESSAGE
from superagentx.computer_use.browser.state import BrowserState
from superagentx.computer_use.browser.models import AgentStepInfo, ActionResult


async def get_user_message(
        state: BrowserState,
        step_info: AgentStepInfo,
        action_result: list[ActionResult],
        use_vision: bool = False
):
    include_attributes = ['title', 'type', 'name', 'role', 'aria-label', 'placeholder', 'value', 'alt',
                          'aria-expanded', 'data-date-format']

    elements_text = state.element_tree.clickable_elements_to_string(
        include_attributes=include_attributes)

    has_content_above = (state.pixels_above or 0) > 0
    has_content_below = (state.pixels_below or 0) > 0

    if elements_text != '':
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
        return {
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
        "role": "user",
        "content": state_description
    }


async def show_toast(page, message: str, duration: int = 3000):
    icons = ['🚀', '🔥', '💡', '⭐']
    random_icon = random.choice(icons)
    final_message = f" SuperAgentX Goal:  {random_icon} {message}"

    toast_script = f"""
                (() => {{
                    let toast = document.createElement('div');
                    toast.innerText = "{final_message}";
                    toast.style.position = 'fixed';
                    toast.style.top = '40px';  // 👈 top instead of bottom
                    toast.style.left = '50%';
                    toast.style.transform = 'translateX(-50%)';
                    toast.style.background = 'linear-gradient(45deg, #ff6ec4, #7873f5)';
                    toast.style.color = 'white';
                    toast.style.padding = '16px 24px';
                    toast.style.borderRadius = '16px';
                    toast.style.fontSize = '14px';

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

    await page.evaluate(toast_script)


SYSTEM_MESSAGE = [
    {
        "role": "system",
        "content": f"{BROWSER_SYSTEM_MESSAGE}\n\nNote:\nEnsure to first build the step by step "
                   f"process, once you build the steps then execute the steps use click event "
                   f"for every step to need. Don't give the duplicate json."
    }
]
