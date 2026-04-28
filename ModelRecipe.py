class ModelRecipe:
    def __init__(self):
        self.imageBase64 = ""
        self.title = ""
        self.category = ""
        self.description = ""
        self.ingredients = []

    def toDictionary(self):
        recipe = {
            "imageBase64": self.imageBase64,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "ingredients": self.ingredients,
        }
        return recipe
