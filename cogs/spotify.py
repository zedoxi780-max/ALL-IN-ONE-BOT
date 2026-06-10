import nextcord
from nextcord.ext import commands
import wavelink
import os

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False

class Spotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = None
        
        if SPOTIFY_AVAILABLE:
            client_id = os.getenv("SPOTIFY_CLIENT_ID")
            client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
            if client_id and client_secret and client_id != "your_spotify_client_id_here":
                try:
                    self.sp = spotipy.Spotify(
                        auth_manager=SpotifyClientCredentials(
                            client_id=client_id,
                            client_secret=client_secret
                        )
                    )
                    print("✅ Spotify ready")
                except Exception as e:
                    print(f"⚠️ Spotify: {e}")

    @nextcord.slash_command(name="spotify_playlist", description="Play a Spotify playlist")
    async def spotify_playlist(self, interaction: nextcord.Interaction, playlist_url: str):
        await interaction.response.defer()
        
        if not self.sp:
            await interaction.followup.send("❌ Spotify not configured!", ephemeral=True)
            return
        if not interaction.user.voice:
            await interaction.followup.send("❌ Join voice!", ephemeral=True)
            return

        try:
            if "playlist/" not in playlist_url:
                await interaction.followup.send("❌ Invalid URL!", ephemeral=True)
                return
            
            playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
            results = self.sp.playlist_tracks(playlist_id)

            player: wavelink.Player = interaction.guild.voice_client
            if not player:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)

            added = 0
            for item in results["items"]:
                if not item["track"]:
                    continue
                track = item["track"]
                query = f"{track['name']} {track['artists'][0]['name']}"
                try:
                    tracks = await wavelink.Playable.search(query)
                    if tracks:
                        await player.queue.put_wait(tracks[0])
                        added += 1
                except:
                    pass

            if not player.playing and player.queue:
                await player.play(player.queue.get())
            await interaction.followup.send(f"✅ Added {added} tracks!")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(Spotify(bot))
