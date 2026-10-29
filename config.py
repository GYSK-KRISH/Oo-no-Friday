'''
-----------------------------------------------------------------
             CONFIG.py file 

 this file = the static "brain data" of the bot:
  1. the 5 companion pets (anime edition, obviously)
  2. rank  evolution titles
  3. mood text based on hunger
  4. the progress bar renderer

------------------------------------------------------------------

'''


DATABASE_NAME = "pet_data.db"

# keys cat , dog , fox, horse
# TODO list: IF SOMEONE WNAT TO ADD OWN PET THEY CAN DO 
PET_CATALOG = {
    "cat": {
        "name": "CAT",
        "emoji" : "🐱",
        "ASSEST URL": "assets/pets/bobcat.png",
    },
    "dog": {
        "name": "DOG",
        "emoji": "🐶",
        "ASSEST URL": "assets/pets/dog-bed-cushion.png",
    },
    "fox": {
        "name": "FOX",
        "emoji": "🦊",
        "ASSEST URL": "assets/pets/kitsune-fox-spirit.png",
    },
    "horse": {
        "name": "HORSE",
        "emoji": "🐴",
        "ASSEST URL": "assets/pets/farm-horse-brown.png",
    }

}


# RANK TITLE FOR A LEVEL 
def RANK_TITLE(level: int) -> str:
    if level < 5:
        return "STAGE 1 | YOU HAVE BEEN PROMOTED TO ROOKIE"
    elif level < 10:
        return "STAGE 2 | YOU HAVE BEEN PROMOTED TO ADVANTAGE"
    elif level < 15:
        return "STAGE 3 | YOU HAVE BEEN PROMOTED TO SUPERSTAR"
    elif level < 20:
        return "STAGE 4 | YOU HAVE BEEN PROMOTED TO LEGENDARY"
    elif level < 25:
        return "STAGE 5 | YOU HAVE BEEN PROMOTED TO MASTER"
    else:
        return "STAGE 6 | YOU HAVE BEEN PROMOTED TO PROTAGONIST (Max Aura)"       


# MOOD STATUS
#adding animation later
def MOOD_STATUS(hunger: int) -> str:

    if hunger >= 80:
        return "HAPPY AND FULL ENRGY"
    elif hunger >= 50:
        return " DOING OKKK"
    elif hunger >= 25:
        return " NEED FOOD ."
    elif hunger > 0:
        return " STRAVING...!"
    else:
        return "DEAD................"
    
#RENDER PROGRESS BAR
def RENDER_PROGRESS_BAR(current_val: int, max_val: int, total_blocks: int = 10) -> str:
     
     if max_val <= 0:
        max_val = 1
        ratio = current_val / max_val
        
        if ratio > 1.0:
            ratio = 1.0
        elif ratio < 0.0:
            ratio = 0.0

            filled_count = int(round(ratio * total_blocks))
            bar_string = ""
            for i in range(total_blocks):
                if i < filled_count:
                     bar_string = bar_string + ""
            else:
                bar_string = bar_string + ""

        percentage = int(ratio * 100)
        return f"{bar_string} `{current_val}/{max_val}` ({percentage}%)"

        

def get_pet(pet_name):
   
    if pet_name in PET_CATALOG:
        return PET_CATALOG[pet_name]
    else:
        return PET_CATALOG["cat"]


# Converts seconds to 1h 5m style

def format_playtime(seconds):
    seconds = int(seconds)

    if seconds < 0:
        seconds = 0

    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {minutes}m"