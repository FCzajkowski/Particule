"""Client-side helpers: fetch wrappers and JavaScript utilities"""


def create_fetch_helpers():
    """Generate JavaScript fetch helpers"""
    return """
    <script>
    window.api = {
        async get(url, options = {}) {
            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options
            });
            return await response.json();
        },
        
        async post(url, data, options = {}) {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                body: JSON.stringify(data),
                ...options
            });
            return await response.json();
        },
        
        async put(url, data, options = {}) {
            const response = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                body: JSON.stringify(data),
                ...options
            });
            return await response.json();
        },
        
        async delete(url, options = {}) {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options
            });
            return await response.json();
        }
    };
    </script>
    """


def create_input_mask_js():
    """Generate JavaScript for input masking"""
    return """
    <script>
    window.inputMasks = {
        phone: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 0) {
                    value = value.match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
                    e.target.value = !value[2] ? value[1] : '(' + value[1] + ') ' + value[2] + (value[3] ? '-' + value[3] : '');
                }
            });
        },
        
        date: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 0) {
                    value = value.match(/(\d{0,2})(\d{0,2})(\d{0,4})/);
                    e.target.value = value[1] + (value[2] ? '/' + value[2] : '') + (value[3] ? '/' + value[3] : '');
                }
            });
        },
        
        currency: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/[^\d.]/g, '');
                let parts = value.split('.');
                parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                if (parts.length > 1) {
                    parts[1] = parts[1].substring(0, 2);
                }
                e.target.value = ' + parts.join('.');
            });
        }
    };
    </script>
    """
