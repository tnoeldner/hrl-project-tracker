import importlib
import data_manager
importlib.reload(data_manager)
print('DB connection used:', data_manager.engine.url)
