import random
import together
import base64
import io
import os


from dotenv import load_dotenv
from interactions import Client, Intents, listen
from interactions import slash_command, SlashContext, slash_option, OptionType, SlashCommandChoice, File

load_dotenv()

together.api = os.environ.get('TOGETHER_API_KEY')

bot = Client(intents=Intents.DEFAULT)

models = {
    1: "stabilityai/stable-diffusion-xl-base-1.0",
    2: "runwayml/stable-diffusion-v1-5",
    3: "SG161222/Realistic_Vision_V3.0_VAE",
    4: "prompthero/openjourney",
    5: "wavymulder/Analog-Diffusion"
}


@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@listen()
async def on_message_create(event):
    print(f"message received: {event.message.content}")

@slash_command(name="imagine", description="Start generating images with prompts")
@slash_option(
    name="prompt",
    description="Describe your image and styling as detail as possible",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="model",
    description="Pick different model based on your preference",
    required=False,
    opt_type=OptionType.INTEGER,
    choices=[
        SlashCommandChoice(name="SDXL", value=1),
        SlashCommandChoice(name="SD1.5", value=2),
        SlashCommandChoice(name="Realistic Vision", value=3),
        SlashCommandChoice(name="Openjourney", value=4),
        SlashCommandChoice(name="Analog Diffusion", value=5),
    ]
)
async def my_command_function(ctx: SlashContext, prompt: str, model: int = 1):
    await ctx.defer()

    seed = random.randint(10000000, 99999999)
    model_path = models.get(model, 'stabilityai/stable-diffusion-xl-base-1.0')
    response = together.Image.create(prompt=prompt, model=model_path, steps=85, seed=seed, width=256, height=256)
    encoded_image = response["output"]["choices"][0]
    image_data = base64.b64decode(encoded_image['image_base64'])
    image_file = io.BytesIO(image_data)
    await ctx.send(file=File(image_file, f'{prompt}.png'))

bot.start(os.environ.get('DISCORD_TOKEN'))
