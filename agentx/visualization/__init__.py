import pandas
import webbrowser
import os

from datetime import datetime
from os import PathLike
from pathlib import Path
from enum import Enum
from math import pi
from bokeh.plotting import figure, output_file, show
from bokeh.models import FactorRange
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
from agentx.visualization.exceptions import InvalidChartType


class ChartType(str, Enum):
    LINE = 'line'
    VBAR = 'vbar'
    HBAR = 'hbar'
    PIE = 'pie'
    TABLE = 'table'


class Visualize:

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
                self.verticalBar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.HBAR:
                self.horizontalBar(
                    data=data,
                    output_type=output_type,
                    output_path=output_path,
                    **kwargs
                )
            case ChartType.PIE:
                self.pieChart(
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

    @staticmethod
    def line_chart(
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
        if not output_type:
            output_type = "html"

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
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    @staticmethod
    def verticalBar(
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
        if not output_type:
            output_type = "html"

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
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    @staticmethod
    def horizontalBar(
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
        if not output_type:
            output_type = "html"

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
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    @staticmethod
    def pieChart(
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
        if not output_type:
            output_type = "html"

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
                output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type}"

            output_file(output_path)

            if show_output:
                show(chart)

    @staticmethod
    def table_chart(
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
            output_path = Path('.') / f"{int(datetime.now().timestamp())}.{output_type}"

        table_data.to_html(str(output_path))
        filename = 'file:///' + os.getcwd() + '/' + str(output_path)

        if show_output:
            webbrowser.open_new_tab(filename)
