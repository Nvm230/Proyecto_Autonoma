import yaml
from PIL import Image
import random
import math

def get_free_points():
    with open('/home/nvm/map.yaml', 'r') as f:
        meta = yaml.safe_load(f)
    
    res = meta['resolution']
    ox, oy, _ = meta['origin']
    
    img = Image.open('/home/nvm/map.pgm')
    width, height = img.size
    pixels = img.load()
    
    free_pixels = []
    
    # Simple check for free pixels that have clearance
    clearance = 5 # pixels (5 * 0.05 = 0.25m)
    for y in range(clearance, height - clearance, 5):
        for x in range(clearance, width - clearance, 5):
            is_free = True
            for dy in range(-clearance, clearance+1):
                for dx in range(-clearance, clearance+1):
                    if pixels[x+dx, y+dy] < 250:
                        is_free = False
                        break
                if not is_free:
                    break
            
            if is_free:
                free_pixels.append((x, y))
                
    if not free_pixels:
        print("No valid free space found with clearance!")
        return
        
    random.shuffle(free_pixels)
    p1 = free_pixels[0]
    p2 = free_pixels[len(free_pixels)//2]
    
    # PGM origin is top-left in PIL, but ROS origin is bottom-left
    # ROS uses: x_world = ox + x_pixel * res
    # ROS uses: y_world = oy + (height - y_pixel - 1) * res
    
    def to_world(px, py):
        wx = ox + px * res
        wy = oy + (height - py - 1) * res
        return wx, wy
        
    w1 = to_world(*p1)
    w2 = to_world(*p2)
    
    print(f"Random Point 1: ({w1[0]:.2f}, {w1[1]:.2f})")
    print(f"Random Point 2: ({w2[0]:.2f}, {w2[1]:.2f})")

if __name__ == '__main__':
    get_free_points()
