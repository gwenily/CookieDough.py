import logging
from discord import MessageType, Embed
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import asyncio
from discord.ext import commands

log = logging.getLogger("cogs.pinboard")

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
        if message.channel.overwrites_for(everyone).read_messages is False or message.channel.overwrites_for(fwiend).read_messages is False:
            await message.channel.send(
                '(btw, either @Everyone or Fwiends can\'t see this channel. So I can\'t put that message on the pinboard)',
                delete_after=8)
            return

        async with aiohttp.ClientSession() as session:
            pins = await message.channel.pins()
            for wh_info in await message.guild.webhooks():
                if wh_info.channel == 'pinboard':
                    break
            webhook = Webhook.from_url(wh_info.url, adapter=AsyncWebhookAdapter(session))
            if webhook is None:
                log.error('Unable find a webhook in a #pinboard channel!')
                await message.send('Unable find a webhook in a #pinboard channel!', delete_after=8)
                return

            if pins[0].author.color.value == 0x000000:
                embdcolor = 0xb9bbbe
            else:
                embdcolor = pins[0].author.color

            enbd = Embed(
                description=f'[Jump To Message!]({pins[0].jump_url})\n(By {pins[0].author.mention} in <#{pins[0].channel.id}>)',
                color=embdcolor)
            if len(pins[0].embeds) > 0:

                if pins[0].embeds[0].type == 'video':
                    enbd.set_image(url=f'{pins[0].embeds[0].thumbnail.url}')
                    enbd.add_field(name='This pin has a video! :movie_camera:',
                                   value=f'**{pins[0].embeds[0].title}**\n[Jump]({pins[0].jump_url}) to watch!',
                                   inline=False)

                elif pins[0].embeds[0].type == 'image':
                    enbd.set_image(url=f'{pins[0].embeds[0].thumbnail.url}')

                elif pins[0].embeds[0].type == 'gifv':
                    if pins[0].embeds[0].provider.name == 'Giphy':
                        enbd.set_image(url=f'{pins[0].embeds[0].url}')
                    else:
                        enbd.set_image(url=f'{pins[0].embeds[0].thumbnail.proxy_url}')
                    if pins[0].embeds[0].provider.name == 'Tenor':
                        enbd.add_field(name='This pin has a video! :movie_camera:',
                                       value=f'[Jump]({pins[0].jump_url}) to watch!',
                                       inline=False)

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
                                       inline=False)
                else:
                    if len(pins[0].embeds[0].image) > 0:
                        enbd.set_image(url=pins[0].embeds[0].image.url)
                    elif len(pins[0].embeds[0].thumbnail) > 0:
                        enbd.set_image(url=pins[0].embeds[0].thumbnail.url)
                        enbd.add_field(name='This pin may have a video! :movie_camera:',
                                       value=f'[Jump]({pins[0].jump_url}) to watch!',
                                       inline=False)
                    enbd.add_field(name='** **',
                                   value=f'**{pins[0].embeds[0].title}**\n{pins[0].embeds[0].description}',
                                   inline=False)

            if len(pins[0].attachments) > 0:
                if pins[0].attachments[0].filename.endswith(('.png', '.jpg', '.gif', '.jpeg', '.webp')):
                    enbd.set_image(url=f'{pins[0].attachments[0].url}')

                elif pins[0].attachments[0].filename.endswith(('.mp4', '.webm')):
                    enbd.set_image(
                        url=f'{pins[0].attachments[0].proxy_url}?format=jpeg&width={pins[0].attachments[0].width}&height={pins[0].attachments[0].height}')
                    enbd.add_field(name='This pin could have a video! :movie_camera:',
                                   value=f'[Jump]({pins[0].jump_url}) to watch!',
                                   inline=False)

                elif pins[0].attachments[0].filename.endswith('.mp3'):
                    enbd.add_field(name='This pin has a sound file! :musical_note:',
                                   value=f'**{pins[0].attachments[0].filename}**\n[Jump]({pins[0].jump_url}) to listen!',
                                   inline=False)

                else:
                    enbd.add_field(name=f'This pin has an unembeddable file! :dividers:',
                                   value=f'**{pins[0].attachments[0].filename}**\n[Jump]({pins[0].jump_url}) to see it!',
                                   inline=False)

            if len(pins[0].embeds) + len(pins[0].attachments) > 1:
                enbd.add_field(name='This Pin Has _**Multiple Files**_ :dividers:',
                               value=f'[Jump]({pins[0].jump_url}) to see all of them!',
                               inline=False)

            if len(pins[0].content) > 0:
                enbd.add_field(name='** **', value=f'{pins[0].content}')

            await webhook.send(avatar_url=f'{pins[0].author.avatar_url}',
                               username=pins[0].author.display_name,
                               embed=enbd)

            keeppin = await message.channel.send('Do you want me to keep the message pinned in here? (yes/no)')

            def check(m):
                return m.channel == message.channel and m.author == message.author and m.content.lower() in ('yes', 'no')
            try:
                keeppin_reply = await self.bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await pins[0].unpin()
                await keeppin.delete()
            if keeppin_reply.content.lower() == 'yes':
                await keeppin.delete()
                await keeppin_reply.delete()
            if keeppin_reply.content.lower() == 'no':
                await pins[0].unpin()
                await keeppin.delete()
                await keeppin_reply.delete()
            log.info(f'{message.author} pinned a message in #{message.channel}')


def setup(bot):
    bot.add_cog(AutoMod(bot))