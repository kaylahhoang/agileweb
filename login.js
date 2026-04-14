document.addEventListener('DOMContentLoaded', () => {
    const wrapper = document.getElementById('wrapper');

    wrapper.style.transform = "translateX(0)";

    const showRegister = document.getElementById('showRegister');
    const showLogin = document.getElementById('showLogin');
    

    showRegister.addEventListener('click', () => {
        wrapper.style.transform = "translateX(-100vw)";

        setTimeout(() => {
        wrapper.style.transform = "translateX(-200vw)";
    }, 400);
    });

    

    
    showLogin.addEventListener('click', () => {
        wrapper.style.transform = "translateX(-100vw)";

        setTimeout(() => {
            wrapper.style.transform = "translateX(0)";
        }, 400);
    });

});