from agentx.visualization import Visualize

obj = Visualize()

chart_data = [
    {
        "Apples": 5,
        "Pears": 3,
        "Nectarines": 4,
        "Plums": 2,
        "Grapes": 4,
        "Strawberries": 6
    },
    {
        "Apples": 12,
        "Pears": 42,
        "Nectarines": 1,
        "Plums": 51,
        "Grapes": 9,
        "Strawberries": 21
    }
]


# chart_data = {
#     "Apples": 5,
#     "Pears": 3,
#     "Nectarines": 4,
#     "Plums": 2,
#     "Grapes": 4,
#     "Strawberries": 6
# }

# chart_data = [
#     {
#         "x": [1, 2, 3, 4, 5],
#         "y": [3, 1, 2, 6, 5]
#     },
#     {
#         "x": [12, 2, 3, 6, 5],
#         "y": [42, 1, 22, 6, 3]
#     }
# ]


async def test_visualization():
    await obj.arender_charts(chart_type="pie", data=chart_data, output_type="html", show_output=True)
    # obj.verticalBar(data=chart_data, output_type="html", show_output=True)
