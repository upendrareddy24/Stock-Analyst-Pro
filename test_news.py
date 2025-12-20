from data_orchestrator import DataOrchestrator
import json

orch = DataOrchestrator()
news = orch.get_ticker_news("NVDA")
print(json.dumps(news, indent=2))
