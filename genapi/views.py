import requests
import json

from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
import together
     
@api_view(["POST"])
def generateImage(request):

    prompt = request.data.get('prompt')
    image_width = request.data.get('image_width', 512)
    image_height = request.data.get( 'image_height', 512)
    steps = request.data.get('steps', 20)
    number_of_images = request.data.get('number_of_images', 1)

    endpoint = 'https://api.together.xyz/inference'
    res = requests.post(endpoint, json={
        "model": "stabilityai/stable-diffusion-xl-base-1.0",
        "prompt": prompt,
        "request_type": "image-model-inference",
        "width": image_width,
        "height": image_height,
        "steps": steps,
        "n": number_of_images
    }, headers={
        "Authorization": f"Bearer {settings.API_KEY}",
    })

    return Response(json.loads(res.text))