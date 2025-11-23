import matplotlib.pyplot as plt
import io
import base64
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.patches import FancyBboxPatch

def get_spotify_chart(labels, values, title, xlabel, orientation='h'):
    """
    Generates a high-quality Spotify-style chart.
    Fixes rendering artifacts and clipping issues on top bars.
    """
    # 1. Setup Theme
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans']

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')

    TEXT_COLOR = '#ffffff'
    SUBTLE_GRAY = '#b3b3b3'
    # Gradient: Dark Green to Spotify Bright Green
    color_start = "#115e2f" 
    color_end = "#1db954"

    # 2. Clean Labels
    clean_labels = []
    for label in labels:
        lbl = label.replace("['", "").replace("']", "").replace("', '", ", ")
        clean_labels.append(lbl[:35] + "..." if len(lbl) > 35 else lbl)

    indices = np.arange(len(clean_labels))
    
    # 3. Horizontal Bars
    if orientation == 'h':
        # Custom colormap
        cmap = mcolors.LinearSegmentedColormap.from_list("spotify_grad", [color_start, color_end])

        # Add breathing room for labels on the right
        ax.set_xlim(0, max(values) * 1.15)
        
        # FIX: Explicitly set Y-limits to prevent the top bar from being clipped
        # Indices run from 0 to N-1. We extend limits to -0.6 and N-0.4
        # to ensure the rounded corners of the first and last bars are fully visible.
        ax.set_ylim(-0.6, len(clean_labels) - 0.4)

        for y, v in zip(indices, values):
            # High-res gradient tile (100x256) to prevent X-artifacts
            grad = np.tile(np.linspace(0, 1, 256), (100, 1))

            # Rounded Box Shape
            bbox = FancyBboxPatch(
                (0, y - 0.325), v, 0.65,
                boxstyle="round,pad=0,rounding_size=0.1",
                linewidth=0, color='none'
            )
            ax.add_patch(bbox)

            # Draw gradient clipped to the rounded box
            ax.imshow(
                grad,
                extent=[0, v, y - 0.325, y + 0.325],
                aspect="auto",
                cmap=cmap,
                clip_path=bbox,
                clip_on=True,
                interpolation='bicubic'
            )

            # Value Label
            ax.text(v + 1, y, str(v), color=color_end, fontweight='bold', va='center', fontsize=10)

        # Axis Styling
        ax.set_yticks(indices)
        ax.set_yticklabels(clean_labels, fontsize=10, color=TEXT_COLOR, fontweight='600')
        ax.invert_yaxis() # Rank #1 at top
        
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.set_xlabel(xlabel, color=SUBTLE_GRAY, labelpad=10)

    # 4. Vertical Bars (Fallback for Diversity View)
    else:
        bars = ax.bar(indices, values, width=0.65, color=color_end, alpha=0.9)
        ax.set_xticks(indices)
        ax.set_xticklabels(clean_labels, rotation=45, ha='right', fontsize=9, color=TEXT_COLOR)
        ax.set_ylabel(xlabel, color=SUBTLE_GRAY)
        
        # Add slight padding for vertical bars too
        ax.set_xlim(-0.6, len(clean_labels) - 0.4)
        
        for i, v in enumerate(values):
            ax.text(i, v + 0.5, str(v), color=color_end, fontweight='bold', ha='center')

    # 5. Global Cleanup
    ax.grid(axis='x' if orientation == 'h' else 'y', linestyle='--', alpha=0.1)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, pad=8, colors=SUBTLE_GRAY)
    
    # Title Alignment
    ax.set_title(title, fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=20, loc='left')

    plt.tight_layout()

    # Output
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True, dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_data = buffer.getvalue()
    buffer.close()
    plt.close(fig)

    return base64.b64encode(img_data).decode('utf-8')