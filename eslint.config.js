const neostandard = require('neostandard')

module.exports = [
    ...neostandard({
        env: ['browser'],
    }),
    {
        languageOptions: {
            ecmaVersion: 12,
        },
        rules: {
            '@stylistic/indent': ['error', 4],
            'no-global-assign': ['error', { exceptions: ['alert'] }],
            'no-undef': 'off',
            'n/no-callback-literal': 'off',
        },
    },
]
