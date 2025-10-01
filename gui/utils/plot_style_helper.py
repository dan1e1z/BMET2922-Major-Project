class PlotStyleHelper:
    """Helper class for consistent plot styling across tabs."""
    
    @staticmethod
    def configure_plot_widget(plot_widget, title="", x_label="Time", x_units="s",
                            y_label="", y_units="", grid=True, 
                            mouse_enabled=False, menu_enabled=False):
        """
        Apply standard configuration to a PlotWidget.
        
        Args:
            plot_widget: pg.PlotWidget to configure
            title: Plot title
            x_label: X-axis label
            x_units: X-axis units
            y_label: Y-axis label
            y_units: Y-axis units
            grid: Show grid
            mouse_enabled: Enable mouse interaction
            menu_enabled: Enable context menu
        """
        if title:
            plot_widget.setTitle(title)
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