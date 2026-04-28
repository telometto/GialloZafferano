import base64
import json
import os
import re

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from ModelRecipe import ModelRecipe

debug = False
folderRecipes = "Recipes"


def saveRecipe(linkRecipeToDownload):
    soup = downloadPage(linkRecipeToDownload)
    title = findTitle(soup)

    filePath = calculateFilePath(title)
    if os.path.exists(filePath):
        return

    ingredients = findIngredients(soup)
    description = findDescription(soup)
    category = findCategory(soup)
    imageBase64 = findImage(soup)

    modelRecipe = ModelRecipe()
    modelRecipe.title = title
    modelRecipe.ingredients = ingredients
    modelRecipe.description = description
    modelRecipe.category = category
    modelRecipe.imageBase64 = imageBase64 or ""

    createFileJson(modelRecipe.toDictionary(), filePath)


def findTitle(soup):
    tag = soup.find(attrs={"class": "gz-title-recipe gz-mBottom2x"})
    return tag.text if tag else ""


def findIngredients(soup):
    allIngredients = []
    for tag in soup.find_all(attrs={"class": "gz-ingredient"}):
        link = tag.a.get("href")
        nameIngredient = tag.a.string
        contents = tag.span.contents[0]
        quantityProduct = re.sub(r"\s+", " ", contents).strip()
        allIngredients.append([nameIngredient, quantityProduct])
    return allIngredients


def findDescription(soup):
    steps = []
    for tag in soup.find_all(attrs={"class": "gz-content-recipe-step"}):
        if hasattr(tag.p, "text"):
            steps.append(tag.p.text)
    return "\n".join(steps)


def findCategory(soup):
    for tag in soup.find_all(attrs={"class": "gz-breadcrumb"}):
        category = tag.li.a.string
        return category


def findImage(soup):

    # Find the first picture tag
    pictures = soup.find("picture", attrs={"class": "gz-featured-image"})

    # Fallback: find a div with class `gz-featured-image-video gz-type-photo`
    if pictures is None:
        pictures = soup.find(
            "div", attrs={"class": "gz-featured-image-video gz-type-photo"}
        )

    if pictures is None:
        return None

    imageSource = pictures.find("img")

    if imageSource is None:
        return None

    # Most of the times the url is in the `data-src` attribute
    imageURL = imageSource.get("data-src")

    # Fallback: if not found in `data-src` look for the `src` attr
    # Most likely, recipes which have the `src` attr
    # instead of the `data-src` one
    # are the older ones.
    # As a matter of fact, those are the ones enclosed
    # in <div> tags instead of <picture> tags (supported only on html5 and onward)
    if imageURL is None:
        imageURL = imageSource.get("src")

    if imageURL is None:
        return None

    try:
        response = requests.get(imageURL, timeout=10)
        response.raise_for_status()
        imageToBase64 = base64.b64encode(response.content).decode("utf-8")
        return imageToBase64
    except requests.RequestException:
        return None


def calculateFilePath(title):
    compact_name = title.replace(" ", "_").lower()
    return os.path.join(folderRecipes, compact_name + ".json")


def createFileJson(data, path):
    with open(path, "w") as file:
        file.write(json.dumps(data, ensure_ascii=False))


def downloadPage(linkToDownload):
    response = requests.get(linkToDownload, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    return soup


def downloadAllRecipesFromGialloZafferano():
    totalPages = countTotalPages() + 1
    # for pageNumber in range(1,totalPages):
    for pageNumber in tqdm(range(1, totalPages), desc="pages…", ascii=False, ncols=75):
        linkList = f"https://www.giallozafferano.it/ricette-cat/page{pageNumber}"
        response = requests.get(linkList, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup.find_all(attrs={"class": "gz-title"}):
            link = tag.a.get("href")
            saveRecipe(link)
            if debug:
                break

        if debug:
            break


def countTotalPages():
    numberOfPages = 0
    linkList = "https://www.giallozafferano.it/ricette-cat"
    response = requests.get(linkList, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup.find_all(attrs={"class": "disabled total-pages"}):
        numberOfPages = int(tag.text)
    return numberOfPages


if __name__ == "__main__":
    if not os.path.exists(folderRecipes):
        os.makedirs(folderRecipes)
    downloadAllRecipesFromGialloZafferano()
