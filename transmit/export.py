# 計算結果をjson形式で出力するモジュール
import json

def export_result(tourcar, spot, result):
	payload = {
		"tourcar_status": tourcar ,
		"spot": spot ,
		"result": result
		
	}
	print(json.dumps(payload, ensure_ascii=False))
	return payload
