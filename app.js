const previewImage = document.querySelector("[data-preview-image]");
const previewTitle = document.querySelector("[data-current-title]");
const previewCopy = document.querySelector("[data-current-copy]");
const tourCards = document.querySelectorAll("[data-preview-src]");

tourCards.forEach((card) => {
    card.addEventListener("click", () => {
        tourCards.forEach((item) => item.setAttribute("aria-current", "false"));
        card.setAttribute("aria-current", "true");
        previewImage.src = card.dataset.previewSrc;
        previewImage.alt = card.dataset.previewAlt;
        previewTitle.textContent = card.dataset.previewTitle;
        previewCopy.textContent = card.dataset.previewCopy;
    });
});
