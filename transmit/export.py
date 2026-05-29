import json


def export_result(result):
	payload = {
		"status": "ok",
		"result": result,
	}
	print(json.dumps(payload, ensure_ascii=False))
	return payload
