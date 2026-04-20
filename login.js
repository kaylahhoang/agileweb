document.addEventListener('DOMContentLoaded', () => {
    const wrapper = document.getElementById('wrapper');



    document.getElementById('showRegister').addEventListener('click', () => {

        wrapper.style.transform = "translateX(-100vw)";
    });

    document.getElementById('showLogin').addEventListener('click', () => {
        wrapper.style.transform = "translateX(0)";
    });
});