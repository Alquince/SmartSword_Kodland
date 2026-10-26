const menuButton = document.querySelector(".site-header__toggle");
const navigation = document.querySelector(".main-nav");
const actions = document.querySelector(".site-header__actions");

if (menuButton && navigation && actions) {
    menuButton.addEventListener("click", () => {
        const isOpen = menuButton.getAttribute("aria-expanded") === "true";
        menuButton.setAttribute("aria-expanded", String(!isOpen));
        navigation.classList.toggle("main-nav--open");
        actions.classList.toggle("site-header__actions--open");
    });
}
