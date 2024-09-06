import os
import webbrowser
from datetime import datetime
from enum import Enum
from itertools import dropwhile
from math import pi
from os import PathLike
from pathlib import Path

import pandas
from bokeh.models import FactorRange
from bokeh.palettes import Category20c
from bokeh.plotting import figure, output_file, show
from bokeh.transform import cumsum

from agentx.utils.helper import sync_to_async, iter_to_aiter
from agentx.visualization.exceptions import InvalidChartType


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
        self.output_type = output_type  or "html"

    def render_charts(
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
                self.line_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.VBAR:
                self.vertical_bar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.HBAR:
                self.horizontal_bar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.PIE:
                self.pie_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.TABLE:
                self.table_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case _:
                raise InvalidChartType(f'Invalid chart type `{chart_type}`')

    def line_chart(
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

        for items in data:
            x = items["x"]
            y = items["y"]

            chart = figure(
                title=title,
                x_axis_label="x",
                y_axis_label="y",
                outer_width=outer_width,
                outer_height=outer_height
            )
            chart.line(
                x,
                y,
                line_width=line_width,
                color=color
            )

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    def vertical_bar(
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
        if not title:
            title = "VerticalBar Chart"
        if not width:
            width = 0.7
        if not color:
            color = "#1890ff"

        if isinstance(data, dict):
            data = [data]

        for items in data:
            x = list(items.keys())
            top = list(items.values())

            chart = figure(
                x_range=x,
                title=title
            )
            chart.vbar(
                x=x,
                top=top,
                width=width,
                color=color
            )

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    def horizontal_bar(
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
        if not title:
            title = "HorizontalBar Chart"
        if not color:
            color = "#1890ff"
        if not height:
            height = 0.7

        if isinstance(data, dict):
            data = [data]

        for items in data:
            x = list(items.keys())
            right = list(items.values())

            chart = figure(
                y_range=FactorRange(factors=x),
                title=title
            )
            chart.hbar(
                y=x,
                right=right,
                height=height,
                color=color
            )

            if not output_path:
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    def pie_chart(
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
        if not title:
            title = "Pie Chart"
        if not line_color:
            line_color = "white"
        if not fill_color:
            fill_color = "color"

        if isinstance(data, dict):
            data = [data]

        for index, items in enumerate(data):
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
            chart.wedge(
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

            output_file(output_path)

            if show_output:
                show(chart)

    def table_chart(
            self,
            *,
            data: dict | list,
            show_output: bool = False,
            output_type: str | None = None,
            output_path: str | PathLike[str]
    ):
        if isinstance(data, dict):
            data = [data]

        table_data = pandas.DataFrame(data)

        if not output_path:
            output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

        table_data.to_html(str(output_path))
        filename = 'file:///' + os.getcwd() + '/' + str(output_path)

        if show_output:
            webbrowser.open_new_tab(filename)

    async def arender_charts(
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
                await self.aline_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.VBAR:
                await self.avertical_bar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.HBAR:
                await self.ahorizontal_bar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.PIE:
                await self.apie_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.TABLE:
                await self.atable_chart(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case _:
                raise InvalidChartType(f'Invalid chart type `{chart_type}`')

    async def aline_chart(
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

    async def avertical_bar(
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

    async def ahorizontal_bar(
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

    async def apie_chart(
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

    async def atable_chart(
            self,
            *,
            data: dict | list,
            show_output: bool = False,
            output_type: str | None = None,
            output_path: str | PathLike[str]
    ):
        if isinstance(data, dict):
            data = [data]

        table_data = await sync_to_async(pandas.DataFrame, data)

        if not output_path:
            output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type or self.output_type}"

        table_data.to_html(str(output_path))
        filename = 'file:///' + os.getcwd() + '/' + str(output_path)

        if show_output:
            await sync_to_async(webbrowser.open_new_tab, filename)
