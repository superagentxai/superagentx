import os
import webbrowser
from datetime import datetime
from enum import Enum
from math import pi
from os import PathLike
from pathlib import Path

import pandas
from bokeh.models import FactorRange
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, show
from bokeh.transform import cumsum

from superagentx.utils.helper import sync_to_async, iter_to_aiter
from superagentx.visualization.exceptions import InvalidChartType


class ChartType(str, Enum):
    LINE = 'line'
    VBAR = 'vbar'
    HBAR = 'hbar'
    PIE = 'pie'
    TABLE = 'table'


class Visualize:

    def __init__(
            self,
            output_type: str | None = None
    ):
        self.output_type = output_type or "html"

    async def render_charts(
            self,
            *,
            chart_type: str | Enum,
            data: dict | list,
            output_type: str | None = None,
            output_path: str | PathLike[str] | None = None,
            **kwargs
    ):
        match chart_type.lower():
            case ChartType.LINE:
                await self.line_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.VBAR:
                await self.vertical_bar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.HBAR:
                await self.horizontal_bar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.PIE:
                await self.pie_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.TABLE:
                await self.table_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case _:
                raise InvalidChartType(f'Invalid chart type `{chart_type}`')

    async def line_chart(
            self,
            *,
            data: dict | list,
            output_type: str | None = None,
            output_path: str | PathLike[str] | None = None,
            title: str | None = None,
            line_width: int | None = None,
            outer_width: int | None = None,
            outer_height: int | None = None,
            color: str | None = None,
            show_output: bool = False
    ):
        """
        Asynchronously generates a line chart based on the provided data inputs.
        This method visualizes trends and patterns over time, allowing for effective data analysis and presentation.

        Parameter:
            data (dict | list): The data to be plotted on the line chart, either as a dictionary or a list.
            output_type (str | None, optional): The format for the output (e.g., 'png', 'pdf'). Defaults to None.
            output_path (str | PathLike[str] | None, optional): The file path where the chart will be saved.
            Defaults to None.
            title (str | None, optional): The title of the line chart. Defaults to None.
            line_width (int | None, optional): The width of the lines in the chart. Defaults to None.
            outer_width (int | None, optional): The overall width of the chart. Defaults to None.
            outer_height (int | None, optional): The overall height of the chart. Defaults to None.
            color (str | None, optional): The color of the lines in the chart. Defaults to None.
            show_output (bool, optional): A flag indicating whether to display the chart after creation.
            Defaults to False.
        """

        if not title:
            title = "Line Chart"
        if not line_width:
            line_width = 2
        if not outer_width:
            outer_width = 400
        if not outer_height:
            outer_height = 400
        if not color:
            color = "#1890ff"

        if isinstance(data, dict):
            data = [data]

        async for items in iter_to_aiter(data):
            x = items["x"]
            y = items["y"]

            chart = figure(
                title=title,
                x_axis_label="x",
                y_axis_label="y",
                outer_width=outer_width,
                outer_height=outer_height
            )
            await sync_to_async(
                chart.line,
                x,
                y,
                line_width=line_width,
                color=color
            )

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            await sync_to_async(output_file, output_path)

            if show_output:
                await sync_to_async(show, chart)

    async def vertical_bar(
            self,
            *,
            data: dict | list,
            output_type: str | None = None,
            output_path: str | PathLike[str] | None = None,
            title: str | None = None,
            width: float | None = None,
            color: str | None = None,
            show_output: bool = False
    ):
        """
            Asynchronously generates a vertical bar chart based on the provided data inputs.
            This method visualizes categorical data, allowing for easy comparison across different groups or categories.

            Parameter:
                data (dict | list): The data to be plotted in the vertical bar chart, either as a dictionary or a list.
                output_type (str | None, optional): The format for the output (e.g., 'png', 'pdf'). Defaults to None.
                output_path (str | PathLike[str] | None, optional): The file path where the chart will be saved.
                Defaults to None.
                title (str | None, optional): The title of the vertical bar chart. Defaults to None.
                width (float | None, optional): The width of the bars in the chart. Defaults to None.
                color (str | None, optional): The color of the bars in the chart. Defaults to None.
                show_output (bool, optional): A flag indicating whether to display the chart after creation.
                Defaults to False.
        """
        if not title:
            title = "VerticalBar Chart"
        if not width:
            width = 0.7
        if not color:
            color = "#1890ff"

        if isinstance(data, dict):
            data = [data]

        async for items in iter_to_aiter(data):
            x = list(items.keys())
            top = list(items.values())

            chart = figure(
                x_range=x,
                title=title
            )
            await sync_to_async(
                chart.vbar,
                x=x,
                top=top,
                width=width,
                color=color
            )

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            await sync_to_async(output_file, output_path)

            if show_output:
                await sync_to_async(show, chart)

    async def horizontal_bar(
            self,
            *,
            data: dict | list,
            output_type: str | None = None,
            output_path: str | PathLike[str] | None = None,
            title: str | None = None,
            color: str | None = None,
            height: float | None = None,
            show_output: bool = False

    ):
        """
            Asynchronously generates a horizontal bar chart based on the provided data inputs.
            This method visualizes categorical data, allowing for easy comparison across different groups or categories.

            Parameter:
                data (dict | list): The data to be plotted in the horizontal bar chart, either as a dictionary or a list.
                output_type (str | None, optional): The format for the output (e.g., 'png', 'pdf'). Defaults to None.
                output_path (str | PathLike[str] | None, optional): The file path where the chart will be saved.
                Defaults to None.
                title (str | None, optional): The title of the horizontal bar chart. Defaults to None.
                color (str | None, optional): The color of the bars in the chart. Defaults to None.
                height (float | None, optional): The height of the bars in the chart. Defaults to None.
                show_output (bool, optional): A flag indicating whether to display the chart after creation.
                Defaults to False.
        """
        if not title:
            title = "HorizontalBar Chart"
        if not color:
            color = "#1890ff"
        if not height:
            height = 0.7

        if isinstance(data, dict):
            data = [data]

        async for items in iter_to_aiter(data):
            x = list(items.keys())
            right = list(items.values())

            chart = figure(
                y_range=FactorRange(factors=x),
                title=title
            )
            await sync_to_async(
                chart.hbar,
                y=x,
                right=right,
                height=height,
                color=color
            )

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            await sync_to_async(output_file, output_path)

            if show_output:
                await sync_to_async(show, chart)

    async def pie_chart(
            self,
            *,
            data: dict | list,
            output_type: str | None = None,
            output_path: str | PathLike[str] | None = None,
            title: str | None = None,
            line_color: str | None = None,
            fill_color: str | None = None,
            show_output: bool = False
    ):
        """
            Asynchronously generates a pie chart based on the provided data inputs.
            This method visualizes proportions of categories, allowing for easy understanding of relative
            sizes within a whole.

            Parameter:
                data (dict | list): The data to be plotted in the pie chart, either as a dictionary or a list.
                output_type (str | None, optional): The format for the output (e.g., 'png', 'pdf'). Defaults to None.
                output_path (str | PathLike[str] | None, optional): The file path where the chart will be saved.
                Defaults to None.
                title (str | None, optional): The title of the pie chart. Defaults to None.
                line_color (str | None, optional): The color of the pie chart borders. Defaults to None.
                fill_color (str | None, optional): The fill color for the pie slices. Defaults to None.
                show_output (bool, optional): A flag indicating whether to display the chart after creation.
                Defaults to False.

        """
        if not title:
            title = "Pie Chart"
        if not line_color:
            line_color = "white"
        if not fill_color:
            fill_color = "color"

        if isinstance(data, dict):
            data = [data]

        async for index, items in iter_to_aiter(enumerate(data)):
            data = pandas.Series(items).reset_index(name='value').rename(columns={'index': 'key'})
            data['angle'] = data['value'] / data['value'].sum() * 2 * pi
            data['color'] = Category20c[len(items)]
            chart = figure(
                title=title,
                tools="hover",
                toolbar_location=None,
                tooltips="@key:@value",
                x_range=(-0.5, 1.0)
            )
            await sync_to_async(
                chart.wedge,
                x=0,
                y=0,
                radius=0.4,
                start_angle=cumsum('angle', include_zero=True),
                end_angle=cumsum('angle'),
                line_color=line_color,
                fill_color=fill_color,
                legend_field="key",
                source=data
            )
            chart.axis.axis_label = None
            chart.axis.visible = False
            chart.grid.grid_line_color = None

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            await sync_to_async(output_file, output_path)

            if show_output:
                await sync_to_async(show, chart)

    async def table_chart(
            self,
            *,
            data: dict | list,
            show_output: bool = False,
            output_type: str | None = None,
            output_path: str | PathLike[str]
    ):
        """
        Asynchronously generates a table chart based on the provided data inputs.
        This method displays data in a structured tabular format, facilitating easy comparison and analysis of
        values across different categories.

        Parameter:
            data (dict | list): The data to be displayed in the table chart, either as a dictionary or a list.
            show_output (bool, optional): A flag indicating whether to display the table chart after creation.
            Defaults to False.
            output_type (str | None, optional): The format for the output (e.g., 'html', 'csv'). Defaults to None.
            output_path (str | PathLike[str]): The file path where the table chart will be saved.
        """
        if isinstance(data, dict):
            data = [data]

        table_data = await sync_to_async(pandas.DataFrame, data)

        if not output_path:
            output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

        table_data.to_html(str(output_path))
        filename = 'file:///' + os.getcwd() + '/' + str(output_path)

        if show_output:
            await sync_to_async(webbrowser.open_new_tab, filename)

    def __dir__(self):
        return (
            "line_chart",
            "vertical_bar",
            "horizontal_bar",
            "pie_chart",
            "table_chart"
        )
