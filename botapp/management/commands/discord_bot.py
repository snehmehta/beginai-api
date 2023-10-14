from django.core.management.base import BaseCommand

import base64
import together
import io
import random
import discord
from django.conf import settings

from botapp.management.commands.prompts import make_prompt

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

description = """BeginBot, a powerful generative AI bot."""

models = {
    1: "stabilityai/stable-diffusion-xl-base-1.0",
    2: "stabilityai/stable-diffusion-2-1",
    3: "runwayml/stable-diffusion-v1-5",
    4: "SG161222/Realistic_Vision_V3.0_VAE",
    5: "prompthero/openjourney",
    6: "wavymulder/Analog-Diffusion",
}


class Command(BaseCommand):
    help = "Run your Discord bot"

    def handle(self, *args, **options):
    
        bot = discord.Bot()

        @bot.event
        async def on_ready():
            print(f"Logged in as {bot.user.name} ({bot.user.id})")
            print("------")

        @bot.command(
            name="imagine",
            description="Generate an image based on your detailed prompt",
        )
        async def visual(
            ctx: discord.ApplicationContext,
            prompt: discord.Option(str, description="What do you want to generate?"),
            style: discord.Option(
                str,
                choices=[
                    "No Style Preset",
                    "Cinematic",
                    "Low Poly",
                    "Anime",
                    "Oilpainting",
                    "Cute",
                    "Comic",
                    "Steampunk",
                    "Vintage",
                    "Natural",
                    "Cyberpunk",
                    "Watercolor",
                    "Apocalyptic",
                    "Fantasy",
                ],
                description="In which style should the image be?",
            ),
            model: discord.Option(
                str,
                choices=[
                    "SDXL",
                    "SD2.1",
                    "SD1.5",
                    "Realistic Vision",
                    "Openjourney",
                    "Analog Diffusion",
                ],
                description="Select the model",
            ),
            negative_prompt: discord.Option(
                str, description="What do you want to avoid?", default=""
            ),
        ):
            if ctx.guild is None:
                await ctx.respond("This command cannot be used in direct messages.")
                return
            await ctx.defer()

            seed = random_seed()
            if not negative_prompt:
                negative_prompt = "Default"

            title_prompt = prompt
            if len(title_prompt) > 150:
                title_prompt = title_prompt[:150] + "..."
            embed = discord.Embed(
                title="Prompt: " + title_prompt,
                description=f"Style: `{style}`\Size: `512x512`\nSeed: `{seed}`\nNegative Prompt: `{negative_prompt}`!",
                color=discord.Colour.blurple(),
            )
            prompt, negativeprompt = make_prompt(prompt, style)
            await ctx.respond("Generating image...", ephemeral=True, delete_after=3)
            model_path = models.get(model, "stabilityai/stable-diffusion-2-1")
            response = together.Image.create(
                prompt=prompt,
                negative_prompt=negativeprompt,
                model=model_path,
                steps=100,
                seed=seed,
                width=512,
                height=512,
            )
            encoded_image = response["output"]["choices"][0]
            image = io.BytesIO(base64.b64decode(encoded_image["image_base64"]))

            if len(prompt) > 100:
                prompt = prompt[:100]

            message = await ctx.respond(
                f"<@{ctx.author.id}>'s Generations:",
                file=discord.File(image, filename=f"{prompt}.png"),
                embed=embed,
            )
            await message.add_reaction("👍")
            await message.add_reaction("👎")

        bot.run(settings.DISCORD_TOKEN)


def random_seed():
    return random.randint(0, 1_000_000_000_000)
