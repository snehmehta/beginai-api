import together
import json

from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from . import helpers

@api_view(["GET"])
def models(request):

    model_list = []

    raw_model_list = cache.get("model_list")

    if raw_model_list is None:
        raw_model_list = together.Models.list()
        cache.set('raw_model_list', raw_model_list, 86400) # cached for 24 hours
    
    for model in raw_model_list:
        if "display_type" in model and model['display_type'] == 'image':
            continue

        model_list.append({
            'name': model.get('display_name',''),
            'model': model.get('name',''),
            'description': model.get('description',''),
            'type': model.get('display_type', ''),
            'created_at': model.get('created_at', ''),
            'updated_at': model.get('update_at', ''),
            'parameter_size': helpers.get_size(model.get('num_parameters', ''))
        })

    result = {
        'num_of_models': len(model_list),
        'models': model_list,
    }
    
    return Response(result)


@api_view(["POST"])
def generate(request: Request):

    prompt = request.data.get('prompt')
    model = request.data.get('model', 'NousResearch/Nous-Hermes-Llama2-13b')
    temperature = request.data.get('temperature')

    try:
        output = together.Complete.create(
            prompt=prompt,
            model=model,
            # temperature=temperature,
            max_tokens=1024,
        )    
        return Response(output)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)