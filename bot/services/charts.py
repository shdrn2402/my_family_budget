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
    Generates a pie chart and returns the file path.
    Data format: [{"label": "Food", "value": 150.5}, ...]
    """
    ensure_plots_dir()
    
    labels = [item["label"] for item in data]
    values = [float(item["value"]) for item in data]
    
    plt.figure(figsize=(10, 7))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, shadow=True)
    plt.title(title)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    filename = f"pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(PLOTS_DIR, filename)
    
    plt.savefig(filepath)
    plt.close()
    
    logger.info(f"Pie chart generated: {filepath}")
    return filepath

def generate_bar_chart(data: List[Dict[str, Any]], title: str = "Expenses Dynamics", xlabel: str = "", ylabel: str = "Amount (₪)") -> str:
    """
    Generates a bar chart and returns the file path.
    Data format: [{"label": "Jan", "value": 1000}, ...]
    """
    ensure_plots_dir()
    
    labels = [item["label"] for item in data]
    values = [float(item["value"]) for item in data]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, values, color='skyblue', edgecolor='navy')
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.05, f'{yval:.2f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    filename = f"bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(PLOTS_DIR, filename)
    
    plt.savefig(filepath)
    plt.close()
    
    logger.info(f"Bar chart generated: {filepath}")
    return filepath
