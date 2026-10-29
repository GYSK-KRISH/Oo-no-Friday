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

# keys cat , dog , fox,horse, slime
#TODO : IF SOMEONE WNAT TO ADD OWN PET THEY CAN DO 


PET_CATALOG = {
    "CAT" : {
        "specie"
    },
    "DOG": {

    },
    "FOX" : {

       },
    "HORSE" :{

    },
    "SLIME " :{

    }
}


# RANK TITLE FOR A LEVEL 
def get_evolution_title(level : int) -> str: 
    if level < 5:
        return " STAGE 1 | YOU ARE GET PROMATED TO ROOKIE "
    elif level >= 5 and level < 10:
        return "STAGE 2 | YOU ARE GET PROMATED TO ADVANTAGE "
    elif level >=10 and level < 15:
        return "STAGE 3 | YOU ARE GET PROMATED TO SUPERSTAR "
    elif level >= 15 and level < 20:
        return "STAGE 4 | YOU ARE GET PROMATED TO LEGENDARY "
    elif level >=20 and level < 25:
        return "STAGE 5 | YOU ARE GET PROMATED TO MASTER "
    else:
        return "STAGE 6 |  Protagonist (Max Aura) "        


# MOOD STATUS
#adding animation 

def get_mood_status(hunger : int ) -> str:
    if hunger >= 80:
        return ""
    elif hunger >= 50:
        return ""
    elif hunger >= 25:
        return ""
    elif hunger > 0:
        return ""
    else:
        return ""
    


def render_progress_bar(current_val: int, max_val: int, total_blocks: int = 10) -> str:
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
                     bar_string = bar_string + "......."
            else:
                bar_string = bar_string + "##"

        percentage = int(ratio * 100)
        return f"{bar_string} `{current_val}/{max_val}` ({percentage}%)"

            


            


        

    
  
if __name__ == "__main__":
    print("=== PET ROSTER ===")
    for key, pet in PET_CATALOG.items():
        print(f"  {pet['emoji']} {key:6} -> {pet['species_name']} (atk {pet['base_atk']})")

    print()
    print("=== RANK CHECK ===")
    test_levels = [1, 4, 5, 11, 12, 24, 25, 39, 40, 99]
    for lvl in test_levels:
        print(f"  lvl {lvl:>3} -> {get_evolution_title(lvl)}")

    print()
    print("=== BAR CHECK ===")
    print("  " + render_progress_bar(0, 100))
    print("  " + render_progress_bar(37, 100))
    print("  " + render_progress_bar(100, 100))
    print("  " + render_progress_bar(999, 100))   # should clamp to 100%
    print("  " + render_progress_bar(50, 0))      # should NOT crash
