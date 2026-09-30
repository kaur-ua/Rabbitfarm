document.addEventListener("DOMContentLoaded", () => {
    const breedField = document.getElementById("id_breed");
    const conditionalClassField = document.getElementById(
        "conditional-class-field"
    );

    if (!breedField || !conditionalClassField) {
        return;
    }

    function updateConditionalClassVisibility() {
        const breed = breedField.value.trim().toLowerCase();
        const normalizedBreed = breed.replace(/[\s-]+/g, "");

        const isUnknownBreed =
            normalizedBreed.includes("невідом") ||
            normalizedBreed.includes("unknown");

        conditionalClassField.style.display =
            isUnknownBreed ? "" : "none";
}

    breedField.addEventListener("input", updateConditionalClassVisibility);
    breedField.addEventListener("change", updateConditionalClassVisibility);

    updateConditionalClassVisibility();
});