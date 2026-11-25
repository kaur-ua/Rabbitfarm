
document.addEventListener("DOMContentLoaded", () => {
    // Existing breed-dependent field visibility
    const breedField = document.getElementById("id_breed");
    const conditionalClassField = document.getElementById(
        "conditional-class-field"
    );

    if (breedField && conditionalClassField) {
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
    }

    // Existing parent clear buttons
    document.querySelectorAll("[data-clear-parent]").forEach((button) => {
        button.addEventListener("click", () => {
            const fieldId = `id_${button.dataset.clearParent}`;
            const parentField = document.getElementById(fieldId);

            if (parentField) {
                parentField.value = "";
                parentField.dispatchEvent(
                    new Event("change", { bubbles: true })
                );
            }
        });
    });

        
    // Duplicate parent warning — manual check only
    const modal = document.getElementById("duplicate-parent-modal");
    const confirmButton = document.getElementById(
        "duplicate-parent-confirm"
    );
    const checkButton = document.getElementById(
        "check-duplicate-parents"
    );
    const resultMessage = document.getElementById(
        "parent-check-result"
    );

    if (!modal || !confirmButton || !checkButton) return;

    const checkUrl = modal.dataset.checkUrl;
    const originField = document.getElementById("id_origin_source");

    const parents = [
        {
            nameField: document.getElementById("id_mother_manual"),
            nodeField: document.getElementById("id_mother_node"),
            sex: "F",
        },
        {
            nameField: document.getElementById("id_father_manual"),
            nodeField: document.getElementById("id_father_node"),
            sex: "M",
        },
    ];

    const modalContent = modal.querySelector(".modal-content");

    modal.style.cssText = `
        display: none;
        position: fixed;
        inset: 0;
        z-index: 1055;
        background: rgba(0, 0, 0, 0.5);
        align-items: center;
        justify-content: center;
        padding: 20px;
    `;

    if (modalContent) {
        modalContent.style.cssText = `
            background: white;
            color: #212529;
            padding: 24px;
            border-radius: 8px;
            max-width: 480px;
            width: 100%;
        `;
    }

    function showModal() {
        modal.style.display = "flex";
        confirmButton.focus();
    }

    function hideModal() {
        modal.style.display = "none";
    }

    confirmButton.addEventListener("click", hideModal);

    async function checkParent(parent, breed, origin) {
        const name = parent.nameField?.value.trim();

        if (!name) {
            return false;
        }

        const params = new URLSearchParams({
            name,
            sex: parent.sex,
            breed,
            origin,
        });

        const response = await fetch(`${checkUrl}?${params}`, {
            method: "GET",
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();
        return data.exists;
    }

    checkButton.addEventListener("click", async () => {
        const breedField = document.getElementById("id_breed");

        if (resultMessage) {
            resultMessage.textContent = "";
        }

        if (!checkUrl || !originField || !breedField) {
            if (resultMessage) {
                resultMessage.textContent =
                    "Не вдалося виконати перевірку. Перевірте форму.";
            }
            return;
        }

        const breed = breedField.value.trim();
        const origin = originField.value.trim();

        if (!breed || !origin) {
            if (resultMessage) {
                resultMessage.textContent =
                    "Спочатку заповніть породу та ферму походження.";
            }
            return;
        }

        checkButton.disabled = true;
        checkButton.textContent = "Перевіряємо...";

        try {
            const results = await Promise.all(
                parents.map(parent =>
                    checkParent(parent, breed, origin)
                )
            );

            if (results.some(Boolean)) {
                showModal();
            } else if (resultMessage) {
                resultMessage.textContent =
                    "Збігів не знайдено. Можна продовжувати.";
            }
        } catch (error) {
            console.error("Duplicate parent check failed:", error);

            if (resultMessage) {
                resultMessage.textContent =
                    "Помилка перевірки. Спробуйте ще раз.";
            }
        } finally {
            checkButton.disabled = false;
            checkButton.textContent = "Перевірити батьків";
        }
    });

        parents.forEach(parent => {
        if (parent.nodeField) {
            parent.nodeField.addEventListener("change", () => {
                if (parent.nodeField.value && parent.nameField) {
                    parent.nameField.value = "";
                }
            });
        }
    });
});
  
