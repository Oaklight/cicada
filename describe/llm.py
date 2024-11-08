import openai
import yaml


class LLM:
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

        self.user_prompt_template = prompt_templates.get("user_prompt_template", "")
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

    def extract_object_description(self, generated_description: str) -> str:
        prompt = self.user_prompt_template.format(
            generated_description=generated_description
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt_template},
                {"role": "user", "content": prompt},
            ],
            **self.model_kwargs
        )
        return response.choices[0].message.content.strip()
