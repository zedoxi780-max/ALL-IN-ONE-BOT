import nextcord
from nextcord.ext import commands
import wavelink

class Music(commands.Cog):
    """Music player commands for Discord"""
    
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="play", 
        description="Play a song from YouTube, Spotify, or SoundCloud"
    )
    async def play(self, interaction: nextcord.Interaction, query: str):
        """Play a song - supports YouTube, Spotify, SoundCloud and more"""
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ You must be in a voice channel!", ephemeral=True)
            return

        try:
            player: wavelink.Player = interaction.guild.voice_client
            if not player:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            elif player.channel != interaction.user.voice.channel:
                await interaction.followup.send("❌ Bot is already in a different voice channel!", ephemeral=True)
                return

            # Search for the track
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                await interaction.followup.send(f"❌ No results found for '{query}'", ephemeral=True)
                return

            track = tracks[0]
            await player.queue.put_wait(track)

            if player.playing:
                await interaction.followup.send(f"✅ Added to queue: **{track.title}** by **{track.author}**")
            else:
                await player.play(player.queue.get())
                await interaction.followup.send(f"🎵 Now playing: **{track.title}** by **{track.author}**")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

    @nextcord.slash_command(name="pause", description="Pause the current song")
    async def pause(self, interaction: nextcord.Interaction):
        """Pause the music"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        if player.paused:
            await interaction.response.send_message("⏸️ Music is already paused", ephemeral=True)
            return
        await player.pause(True)
        await interaction.response.send_message("⏸️ Music paused")

    @nextcord.slash_command(name="resume", description="Resume the current song")
    async def resume(self, interaction: nextcord.Interaction):
        """Resume the music"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        if not player.paused:
            await interaction.response.send_message("▶️ Music is already playing", ephemeral=True)
            return
        await player.pause(False)
        await interaction.response.send_message("▶️ Music resumed")

    @nextcord.slash_command(name="stop", description="Stop the music and clear the queue")
    async def stop(self, interaction: nextcord.Interaction):
        """Stop the music and clear queue"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        await player.stop()
        player.queue.clear()
        await interaction.response.send_message("⏹️ Music stopped and queue cleared")

    @nextcord.slash_command(name="skip", description="Skip to the next song")
    async def skip(self, interaction: nextcord.Interaction):
        """Skip the current song"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)
            await interaction.response.send_message(f"⏭️ Skipped! Now playing: **{next_track.title}**")
        else:
            await player.stop()
            await interaction.response.send_message("⏭️ No more songs in queue")

    @nextcord.slash_command(name="queue", description="Show the current queue")
    async def queue(self, interaction: nextcord.Interaction):
        """Display the music queue"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player or player.queue.is_empty:
            await interaction.response.send_message("📭 Queue is empty", ephemeral=True)
            return
        
        queue_list = ""
        for i, track in enumerate(list(player.queue)[:10], 1):
            queue_list += f"{i}. **{track.title}** - {track.author}\n"
        
        if len(player.queue) > 10:
            queue_list += f"\n... and {len(player.queue) - 10} more songs"
        
        embed = nextcord.Embed(
            title="🎵 Current Queue",
            description=queue_list,
            color=nextcord.Color.purple()
        )
        embed.set_footer(text=f"Total: {len(player.queue)} songs")
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="now", description="Show currently playing song info")
    async def now(self, interaction: nextcord.Interaction):
        """Show the currently playing song"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.current:
            await interaction.response.send_message("❌ Nothing is currently playing", ephemeral=True)
            return
        
        track = player.current
        minutes = track.length // 60000
        seconds = (track.length % 60000) // 1000
        duration = f"{minutes}:{seconds:02d}"
        
        embed = nextcord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}**",
            color=nextcord.Color.purple()
        )
        embed.add_field(name="Artist", value=track.author, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Source", value=track.source or "Unknown", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="volume", description="Set playback volume (0-100)")
    async def volume(self, interaction: nextcord.Interaction, level: int):
        """Set the playback volume"""
        if level < 0 or level > 100:
            await interaction.response.send_message("❌ Volume must be between 0 and 100", ephemeral=True)
            return
        
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        
        await player.set_volume(level)
        await interaction.response.send_message(f"🔊 Volume set to {level}%")

    @nextcord.slash_command(name="disconnect", description="Disconnect bot from voice channel")
    async def disconnect(self, interaction: nextcord.Interaction):
        """Disconnect the bot from voice"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        
        await player.disconnect()
        await interaction.response.send_message("👋 Bot disconnected from voice channel")

    @nextcord.slash_command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: nextcord.Interaction):
        """Shuffle the current queue"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player or player.queue.is_empty:
            await interaction.response.send_message("❌ Queue is empty!", ephemeral=True)
            return
        
        player.queue.shuffle()
        await interaction.response.send_message("🔀 Queue shuffled")

    @nextcord.slash_command(name="clearqueue", description="Clear the entire queue")
    async def clearqueue(self, interaction: nextcord.Interaction):
        """Clear the queue"""
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            await interaction.response.send_message("❌ Bot is not connected!", ephemeral=True)
            return
        
        player.queue.clear()
        await interaction.response.send_message("🗑️ Queue cleared")

def setup(bot):
    bot.add_cog(Music(bot))
