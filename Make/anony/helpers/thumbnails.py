# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from anony import config
from anony.helpers import Track


class Thumbnail:
    def __init__(self):
        self.rect = (500, 500)  # مربع 500x500
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)
        self.font1 = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 48) 
        self.font2 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 36)   
        self.font3 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 32)   
        self.font_vega = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 48) 
        
    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()
        
    async def close(self) -> None:
        await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with self.session.get(url) as resp:
            with open(output_path, "wb") as f:
                f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            

            thumb = Image.open(temp).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            
            blur = thumb.filter(ImageFilter.GaussianBlur(8))
            background = ImageEnhance.Brightness(blur).enhance(.30)
            _rect = ImageOps.fit(thumb, self.rect, method=Image.LANCZOS, centering=(0.5, 0.5))
            
            mask = Image.new("L", self.rect, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, self.rect[0], self.rect[1]), radius=30, fill=255)
            _rect.putalpha(mask)
            background.paste(_rect, (40, 110), _rect)

            glass_size = (self.rect[0] + 40, self.rect[1] + 40)
            glass_overlay = Image.new("RGBA", glass_size, (255, 255, 255, 0))
            glass_draw = ImageDraw.Draw(glass_overlay)
            glass_draw.rounded_rectangle(
                (0, 0, glass_size[0], glass_size[1]), 
                radius=45,  
                fill=(255, 255, 255, 10),
                outline=(255, 255, 255, 25),  
                width=1
            )
            background.paste(glass_overlay, (20, 90), glass_overlay)  
            draw = ImageDraw.Draw(background)
            
            text_start_x = 600  
            text_start_y = 220  

            vega_text = "VEGA & SOUND"
            vega_y = text_start_y - 55  
               
            draw.text((text_start_x + 1, vega_y + 1), vega_text, font=self.font_vega, fill=(0, 0, 0, 40))
            draw.text((text_start_x, vega_y), vega_text, font=self.font_vega, fill=(255, 255, 255, 230))
            title_text = song.title[:55]
            draw.text((text_start_x + 2, text_start_y + 2), title_text, font=self.font1, fill=(0, 0, 0, 50))
            draw.text((text_start_x, text_start_y), title_text, font=self.font1, fill=(255, 255, 255))
            
            channel_y = text_start_y + 70
            channel_text = f"NAME: {song.channel_name[:30]}"
            draw.text((text_start_x + 1, channel_y + 1), channel_text, font=self.font2, fill=(0, 0, 0, 40))
            draw.text((text_start_x, channel_y), channel_text, font=self.font2, fill=(255, 255, 255))
            
            views_y = channel_y + 55
            views_text = f"Views: {song.view_count} "
            draw.text((text_start_x + 1, views_y + 1), views_text, font=self.font3, fill=(0, 0, 0, 40))
            draw.text((text_start_x, views_y), views_text, font=self.font3, fill=(255, 255, 255))
            
            duration_y = views_y + 45
            duration_text = f"Time: {song.duration}"
            draw.text((text_start_x + 1, duration_y + 1), duration_text, font=self.font3, fill=(0, 0, 0, 40))
            draw.text((text_start_x, duration_y), duration_text, font=self.font3, fill=(255, 255, 255))

            background.save(output)
            os.remove(temp)
            return output
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB