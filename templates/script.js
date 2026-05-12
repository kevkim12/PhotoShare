let tagCount = 1;
const tagHolder = document.querySelector("#tag-input");

function addTagInput() {
    if (!tagHolder) {
        return;
    }

    const tagInput = document.createElement("input");
    tagInput.type = "text";
    tagInput.name = "tag" + tagCount;
    tagInput.id = "tag" + tagCount;
    tagInput.placeholder = "Tag " + tagCount;
    tagInput.autocomplete = "off";

    tagHolder.appendChild(tagInput);
    tagCount += 1;
}
