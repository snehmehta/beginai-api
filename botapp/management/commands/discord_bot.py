from django.core.management.base import BaseCommand
from botapp.management.commands.agent import agents, group_agents
from botapp.management.commands.prompts import make_prompt
from django.conf import settings

import base64
import together
import io
import random
import discord
import asyncio
from discord.ext import commands


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


class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_queues = {}
        self.receive_queues = {}
        self.bg_tasks = {}
        self.user_proxys = {}

    async def background_task(self, thread):
        await self.bot.wait_until_ready()
        receive_queue = self.receive_queues[thread.id]
        send_queue = self.send_queues[thread.id]
        while not self.bot.is_closed():
            message = await receive_queue.get()
            async with thread.typing():
                if message:
                    msg = message["message"]
                    for chunk in (msg[i : i + 2000] for i in range(0, len(msg), 2000)):
                        await thread.send(chunk)

    async def run_autogen_logic(
        self, ctx: discord.ApplicationContext, query: str, group_chat: str
    ):
        discord_message = await ctx.send(f"Initialize thread with {group_chat}")
        thread = await discord_message.create_thread(
            name=f"{query[:80]}", auto_archive_duration=60
        )
        send_queue = asyncio.Queue()
        receive_queue = asyncio.Queue()
        self.send_queues[thread.id] = send_queue
        self.receive_queues[thread.id] = receive_queue
        self.bg_tasks[thread.id] = self.bot.loop.create_task(
            self.background_task(thread)
        )

        if group_chat == "python dev and critic":
            user, assistant = group_agents(send_queue, receive_queue)
        else:
            user, assistant = agents(send_queue, receive_queue)

        self.user_proxys[thread.id] = user

        await user.a_initiate_chat(assistant, message=query)

    @commands.slash_command(
        name="autogen", description="Experience the power of conversable agents"
    )
    async def autogen(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(str, description="Write your task in detail?"),
        group_chat: discord.Option(
            str,
            choices=["python dev"],
            description="Select a group which will converse with each other to complete the task",
        ),
    ):
        await ctx.defer()

        await ctx.respond("...")
        self.bot.loop.create_task(self.run_autogen_logic(ctx, query, group_chat))

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        await thread.send("Bot has joined Thread!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.Thread) and not message.author.bot:
            if message.channel.id in self.send_queues:
                await self.send_queues[message.channel.id].put(message.content)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.id in self.send_queues:
            del self.send_queues[thread.id]
        if thread.id in self.bg_tasks:
            self.bg_tasks[thread.id].cancel()
            del self.bg_tasks[thread.id]


class Command(BaseCommand):
    help = "Run your Discord bot"

    def handle(self, *args, **options):
        bot = discord.Bot(intents=intents)

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

        bot.add_cog(QueueCog(bot))
        bot.run(settings.DISCORD_TOKEN)


def random_seed():
    return random.randint(0, 1_000_000_000_000)
