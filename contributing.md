# Contributing to 2-Wheeler Blind Spot Detection

Thank you for considering contributing to this project! 

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- **Clear title** describing the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **System info** (OS, Python version, OpenCV version)
- **Screenshots/videos** if applicable

### Suggesting Enhancements

For feature requests, please include:
- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches did you think about?

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with clear, descriptive commits
4. **Test your changes** thoroughly
5. **Update documentation** if needed
6. **Submit a pull request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/videos for UI changes

### Code Standards

- Follow **PEP 8** style guidelines
- Add **docstrings** to functions and classes
- Include **comments** for complex logic
- Keep functions **small and focused**
- Write **descriptive variable names**

Example:
```python
def calculate_velocity(current_pos, previous_pos, time_delta):
    """
    Calculate velocity vector from position change
    
    Args:
        current_pos: (x, y) current position
        previous_pos: (x, y) previous position
        time_delta: Time elapsed in seconds
        
    Returns:
        (vx, vy) velocity vector in pixels/second
    """
    vx = (current_pos[0] - previous_pos[0]) / time_delta
    vy = (current_pos[1] - previous_pos[1]) / time_delta
    return (vx, vy)
```

### Testing

Before submitting, test with:
- Multiple video sources
- Different lighting conditions
- Various vehicle types
- Edge cases (empty frames, occlusions)

### Areas for Contribution

**Beginner-Friendly:**
- Documentation improvements
- Adding code comments
- Creating test videos
- Writing tutorials

**Intermediate:**
- Performance optimization
- Adding unit tests
- UI improvements
- Configuration options

**Advanced:**
- YOLOv8 integration
- Kalman filter tracking
- Stereo vision support
- Hardware integration

## 📧 Questions?

Open an issue with the `question` label or contact the maintainers.

Thank you for contributing! 🙏
