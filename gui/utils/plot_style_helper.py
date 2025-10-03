class PlotStyleHelper:
    @staticmethod
    def auto_scale_y_axis(plot_widget, x_data, y_data, x_range, padding=0.1, min_limit=None, max_limit=None, scale_mode="auto"):
        """
        Adjust the y-axis of a plot based on the selected scaling mode.

        Args:
            plot_widget: The PlotWidget to scale
            x_data: List/array of x values
            y_data: List/array of y values
            x_range: Tuple (start_x, end_x) for visible window
            padding: Fractional padding to add to y-range
            min_limit: Optional minimum y-axis bound
            max_limit: Optional maximum y-axis bound
            scale_mode: Scaling behaviour
                - "auto": Scale to min/max of visible data (with optional limits)
                - "fixed": Use only min_limit/max_limit if provided, ignore data
                - "none": Do nothing (keep existing y-axis)
        """
        if scale_mode == "none":
            return

        if scale_mode == "fixed":
            if min_limit is not None and max_limit is not None:
                plot_widget.setYRange(min_limit, max_limit, padding=padding)
            return

        # Default: auto mode
        if not x_data or not y_data or len(x_data) != len(y_data):
            return
        start_x, end_x = x_range
        indices = [i for i, t in enumerate(x_data) if start_x <= t <= end_x]
        if not indices:
            return
        window_y = [y_data[i] for i in indices]
        if len(window_y) > 0:
            min_y, max_y = min(window_y), max(window_y)
            if min_limit is not None:
                min_y = max(min_y, min_limit)
            if max_limit is not None:
                max_y = min(max_y, max_limit)
            if min_y != max_y:
                plot_widget.setYRange(min_y, max_y, padding=padding)


    """Helper class for consistent plot styling across tabs."""
    
    @staticmethod
    def configure_plot_widget(plot_widget, title="", x_label="Time", x_units="s",
                          y_label="", y_units="", grid=True, 
                          mouse_enabled=False, menu_enabled=False):
        """
        Configure a PlotWidget with standard settings, including axis labels with optional units.

        Args:
            plot_widget: pg.PlotWidget instance to configure.
            title (str): Plot title.
            x_label (str): Label for the X-axis.
            x_units (str): Units for the X-axis, appended to the label if provided.
            y_label (str): Label for the Y-axis.
            y_units (str): Units for the Y-axis, appended to the label if provided.
            grid (bool): Whether to display a grid.
            mouse_enabled (bool): Enable mouse interaction.
            menu_enabled (bool): Enable context menu.
        """
        if title:
            plot_widget.setTitle(title)
        
        # Set axis labels with units if provided
        plot_widget.setLabel('left', y_label, units=y_units)
        plot_widget.setLabel('bottom', x_label, units=x_units)
        
        if grid:
            plot_widget.showGrid(True, True)
        
        plot_widget.setMouseEnabled(x=mouse_enabled, y=mouse_enabled)
        plot_widget.setMenuEnabled(menu_enabled)

    
    @staticmethod
    def create_legend(plot_widget, offset=(-1, -1)):
        """
        Create and return a legend for the plot.
        
        Args:
            plot_widget: pg.PlotWidget to add legend to
            offset: Legend position offset
            
        Returns:
            pg.LegendItem
        """
        return plot_widget.addLegend(offset=offset)
    
    @staticmethod
    def toggle_legend_visibility(legend, visible):
        """Toggle legend visibility."""
        if legend:
            legend.setVisible(visible)