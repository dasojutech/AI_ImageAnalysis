# # import yaml
# # from pipeline import run_pipeline


# # with open("config/config.yaml") as f:
# #     config = yaml.safe_load(f)

# # print(config)
# # print(config["vector"]["place_name"])

# # # 2️⃣ Call the pipeline
# # run_pipeline(config)
# import os
# import yaml
# from pipeline import run_pipeline
# # Absolute path relative to main.py
# config_path = os.path.join(os.path.dirname(__file__), "../config/config.yaml")

# with open(config_path) as f:
#     config = yaml.safe_load(f)
# run_pipeline(config)

# src/main.py
import os
import yaml
from pipeline import run_pipeline

# Load config from YAML
config_path = os.path.join(os.path.dirname(__file__), "../config/config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

# Now config is defined
run_pipeline(config)