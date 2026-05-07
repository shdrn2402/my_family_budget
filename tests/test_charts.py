import os
import pytest
from bot.services.charts import generate_pie_chart, generate_bar_chart, PLOTS_DIR

def test_generate_pie_chart():
    # Mock data
    data = [
        {"label": "Food", "value": 150.5},
        {"label": "Fuel", "value": 3000.0},
        {"label": "Other", "value": 500.0}
    ]
    
    filepath = generate_pie_chart(data, "Test Pie Chart")
    
    assert os.path.exists(filepath)
    assert filepath.startswith(PLOTS_DIR)
    assert filepath.endswith(".png")
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)

def test_generate_bar_chart():
    # Mock data
    data = [
        {"label": "January", "value": 1000},
        {"label": "February", "value": 1200},
        {"label": "March", "value": 800}
    ]
    
    filepath = generate_bar_chart(data, "Test Bar Chart", xlabel="Months")
    
    assert os.path.exists(filepath)
    assert filepath.startswith(PLOTS_DIR)
    assert filepath.endswith(".png")
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)

def test_ensure_plots_dir_creates_folder():
    # Ensure dir exists (it might already exist from previous tests)
    from bot.services.charts import ensure_plots_dir
    ensure_plots_dir()
    assert os.path.exists(PLOTS_DIR)
    assert os.path.isdir(PLOTS_DIR)
