"""Presets declarativos: destino, residencia y capacidades de generación."""

PRESETS = {
    'ollama': {'name': 'Ollama', 'transport': 'ollama', 'base_url': '', 'data_residency': 'local',
               'secret_name': '', 'response_format': 'json_schema', 'models': {}},
    'deepseek': {'name': 'DeepSeek', 'transport': 'openai', 'base_url': 'https://api.deepseek.com',
                 'data_residency': 'fuera-ue', 'secret_name': 'deepseek_api_key', 'response_format': 'json_object',
                 'models': {'deepseek-chat': 'json_object', 'deepseek-reasoner': 'none'}},
    'mistral': {'name': 'Mistral', 'transport': 'openai', 'base_url': 'https://api.eu.mistral.ai/v1',
                'data_residency': 'ue', 'secret_name': 'mistral_api_key', 'response_format': 'json_schema',
                'models': {'mistral-small-latest': 'json_schema', 'mistral-large-latest': 'json_schema'}},
    'custom': {'name': 'Endpoint personalizado', 'transport': 'openai', 'base_url': '',
               'data_residency': 'desconocida', 'secret_name': 'custom_api_key', 'response_format': 'none', 'models': {}},
}

RESIDENCY_LABELS = {'local': 'local', 'ue': 'UE', 'fuera-ue': 'fuera de la UE', 'desconocida': 'residencia desconocida'}
