import matplotlib.pyplot as plt
import rasterio
import rasterio.plot

def plot_overlay(raster_path, vector_layers, title="AOI + Sentinel-2 + GIS Layers", save_path=None):
    """
    Plots a raster with vector overlays.

    Args:
        raster_path (str): Path to the raster (e.g., Sentinel-2)
        vector_layers (list): List of GeoDataFrames to overlay
        title (str): Plot title
        save_path (str, optional): If given, saves figure to this path

    Returns:
        matplotlib.figure.Figure: The figure object
    """
    fig, ax = plt.subplots(figsize=(10,10))

    # Plot raster
    with rasterio.open(raster_path) as src:
        rasterio.plot.show(src, ax=ax)

    # Plot vector layers
    for layer in vector_layers:
        # Use boundary if available, fallback to normal plot
        if hasattr(layer, "boundary"):
            layer.boundary.plot(ax=ax, edgecolor="red", linewidth=1)
        else:
            layer.plot(ax=ax)

    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    plt.tight_layout()

    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Figure saved to: {save_path}")

    # Show figure
    plt.show(block=True)

    return fig