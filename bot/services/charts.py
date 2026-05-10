import matplotlib.pyplot as plt
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

# Use Agg backend for non-GUI environments (servers)
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

# Directory for temporary plots
PLOTS_DIR = "bot/temp_plots"

def ensure_plots_dir():
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)

def generate_pie_chart(data: List[Dict[str, Any]], title: str = "Expenses Structure") -> str:
    """
    Generates a pie chart. Groups small categories into 'Others' if more than 10 items.
    """
    ensure_plots_dir()
    
    # Sort and group small values
    sorted_data = sorted(data, key=lambda x: x["value"], reverse=True)
    if len(sorted_data) > 10:
        main_data = sorted_data[:9]
        others_value = sum(item["value"] for item in sorted_data[9:])
        main_data.append({"label": "Прочее / Others", "value": others_value})
        display_data = main_data
    else:
        display_data = sorted_data

    labels = [item["label"] for item in display_data]
    values = [float(item["value"]) for item in display_data]
    
    plt.figure(figsize=(10, 8))
    colors = plt.cm.Paired(range(len(labels)))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.title(title, pad=20, fontsize=14)
    plt.axis('equal')
    
    filename = f"pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(PLOTS_DIR, filename)
    plt.savefig(filepath, bbox_inches='tight')
    plt.close()
    return filepath

def generate_bar_chart(data: List[Dict[str, Any]], title: str = "Expenses Dynamics", xlabel: str = "", ylabel: str = "Amount (₪)") -> str:
    """
    Generates a bar chart. Limits to top 15 bars if too many.
    """
    ensure_plots_dir()
    
    # Sort by value to show the most important first
    sorted_data = sorted(data, key=lambda x: x["value"], reverse=True)
    if len(sorted_data) > 15:
        sorted_data = sorted_data[:15]
    
    labels = [item["label"] for item in sorted_data]
    values = [float(item["value"]) for item in sorted_data]
    
    plt.figure(figsize=(12, 7))
    bars = plt.bar(labels, values, color='#3498db', edgecolor='#2980b9', alpha=0.8)
    
    plt.title(title, fontsize=16, pad=20)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(values)*0.01 if values else 0), 
                 f'{yval:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    filename = f"bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(PLOTS_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    return filepath
