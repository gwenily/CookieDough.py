import logging
from discord import MessageType, Embed
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
from discord.ext import commands

log = logging.getLogger("cogs.automod")


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """When a message is pinned, push an embed of that message through a webhook"""
        if message.type != MessageType.pins_add:
            return
        for role in message.guild.roles:
            if role.name.lower() == "@everyone":
                everyone = role
            if role.name.lower() == "fwiend":
                fwiend = role
        if message.channel.overwrites_for(everyone).read_messages or \
                message.channel.overwrites_for(fwiend).read_messages is False:
            await message.channel.send(
                '(btw, either @Everyone or Fwiends can\'t see this channel. So I can\'t put that message on the pinboard)',
                delete_after=8)
            return
        async with aiohttp.ClientSession() as session:
            pins = await message.channel.pins()
            for Webhook in await message.guild.webhooks():
                if Webhook.channel == 'pinboard':
                    Webhook = Webhook
            webhook = Webhook.from_url(Webhook.url, adapter=AsyncWebhookAdapter(session))
            enbd = Embed(
                description=f'[Jump To Message!]({pins[0].jump_url})\n(By {pins[0].author.mention} in <#{pins[0].channel.id}>)',
                color=pins[0].author.color)
            if len(pins[0].embeds) > 0:
                if pins[0].embeds[0].type == 'video':
                    enbd.set_image(url=f'{pins[0].embeds[0].thumbnail.url}')
                    enbd.add_field(name='This pin has a video! :movie_camera:',
                                   value=f'**{pins[0].embeds[0].title}**\n[Jump]({pins[0].jump_url}) to watch!',
                                   inline=True)
                elif pins[0].embeds[0].type == 'image':
                    enbd.set_image(url=f'{pins[0].embeds[0].thumbnail.url}')
                elif pins[0].embeds[0].type == 'rich':
                    enbd.add_field(name='** **',
                                   value=f'[{pins[0].embeds[0].author.name}]({pins[0].embeds[0].author.url})\n{pins[0].embeds[0].description}',
                                   inline=False)
                    if len(pins[0].embeds[0].image) > 0:
                        enbd.set_image(url=pins[0].embeds[0].image.url)
                    elif len(pins[0].embeds[0].thumbnail) > 0:
                        enbd.set_image(url=pins[0].embeds[0].thumbnail.url)
                        enbd.add_field(name='This pin has a video! :movie_camera:',
                                       value=f'[Jump]({pins[0].jump_url}) to watch!',
                                       inline=True)
                else:
                    if len(pins[0].embeds[0].image) > 0:
                        enbd.set_image(url=pins[0].embeds[0].image.url)
                    elif len(pins[0].embeds[0].thumbnail) > 0:
                        enbd.set_image(url=pins[0].embeds[0].thumbnail.url)
                        enbd.add_field(name='This pin could have a video! :movie_camera:',
                                       value=f'[Jump]({pins[0].jump_url}) to watch!',
                                       inline=True)
                    enbd.add_field(name='** **',
                                       value=f'**{pins[0].embeds[0].title}**\n{pins[0].embeds[0].description}',
                                       inline=False)
            if len(pins[0].attachments) > 0:
                if pins[0].attachments[0].filename.endswith(('.png', '.jpg', '.gif', '.jpeg')):
                    enbd.set_image(url=f'{pins[0].attachments[0].url}')
                elif pins[0].attachments[0].filename.endswith(('.mp4', '.webm')):
                    enbd.set_image(
                        url=f'{pins[0].attachments[0].proxy_url}?format=jpeg&width={pins[0].attachments[0].width}&height={pins[0].attachments[0].height}')
                    enbd.add_field(name='This pin could have a video! :movie_camera:',
                                   value=f'[Jump]({pins[0].jump_url}) to watch!',
                                   inline=True)
                elif pins[0].attachments[0].filename.endswith(('.mp3')):
                    enbd.add_field(name='This pin has a sound file! :musical_note:',
                                   value=f'**{pins[0].attachments[0].filename}**\n[Jump]({pins[0].jump_url}) to listen!',
                                   inline=True)
                else:
                    enbd.add_field(name=f'This pin has an unembeddable file! :dividers:',
                                   value=f'**{pins[0].attachments[0].filename}**\n[Jump]({pins[0].jump_url}) to see it!',
                                   inline=True)
            if len(pins[0].embeds) + len(pins[0].attachments) > 1:
                enbd.add_field(name='This Pin Has _**Multiple Files**_ :dividers:',
                               value=f'[Jump]({pins[0].jump_url}) to see all of them!',
                               inline=True)
            if len(pins[0].content) > 0:
                enbd.add_field(name='** **', value=f'{pins[0].content}')
            await webhook.send(avatar_url=f'{pins[0].author.avatar_url}',
                               username=pins[0].author.display_name,
                               embed=enbd)
            log.info(f'{message.author} pinned a message in #{message.channel}')


def setup(bot):
    bot.add_cog(AutoMod(bot))
