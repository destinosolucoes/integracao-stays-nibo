# API Tests

This directory contains tests for the API functionality.

## Setup

Make sure you have the following dependencies installed:

```
pip install pytest pytest-asyncio
```

## Running Tests

Run all tests from the project root:

```
./run_tests.sh
```

Or run pytest directly:

```
pytest api/tests/ -v
```

## Test Structure

- `test_webhook_processor.py`: Tests for the webhook processing functionality
- `conftest.py`: Common fixtures for tests
- `mocks/`: Mock data for tests

## Creating New Tests

When creating new tests:

1. Use appropriate fixtures from `conftest.py`
2. Use mock data from `mocks/` directory
3. Follow the pattern of existing tests
4. Make sure to use patchers for external dependencies 