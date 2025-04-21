import re


def main():
    string = ('```json\n{\n  "current_state": {\n    "evaluation_previous_goal": "Unknown - The current page is a new '
              'tab page. No previous goal to evaluate.",\n    "memory": "Need to find out who won yesterday\'s IPL '
              'match, then go to X and post the results. First step is to search for the IPL result.",'
              '\n    "next_goal": "Search Google to find out who won yesterday\'s IPL match."\n  },\n  "action": [\n  '
              '  {\n      "search_google": {\n        "query": "Who won yesterday\'s IPL match?"\n      }\n    }\n  '
              ']\n}\n```')
    start = '```json\n'
    end = '```'
    if start in string:
        r = re.findall(re.escape(start) + "(.+?)" + re.escape(end), string, re.DOTALL)
        if r:
            string = r[0]

    print(string)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt):
        print("\nUser canceled the [bold yellow][i]pipe[/i]!")
