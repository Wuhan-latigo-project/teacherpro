import os
import argparse
from pathlib import Path

def create_file_tree(directory, prefix="", show_files=True, max_depth=None, current_depth=0):
    """
    Recursively creates a tree representation of files and folders.
    
    Args:
        directory: The directory path to start from
        prefix: Prefix string for tree formatting
        show_files: Whether to show files or just directories
        max_depth: Maximum depth to traverse (None for unlimited)
        current_depth: Current depth in recursion
    """
    if max_depth is not None and current_depth > max_depth:
        return ""
    
    tree = ""
    try:
        # Get all items in the directory
        items = sorted(os.listdir(directory))
        
        # Separate directories and files
        dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
        files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
        
        # Process directories first
        for i, item in enumerate(dirs):
            is_last = (i == len(dirs) - 1) and (not show_files or not files)
            tree += f"{prefix}{'└── ' if is_last else '├── '}{item}/\n"
            
            # Recursively process subdirectories
            new_prefix = prefix + ("    " if is_last else "│   ")
            sub_tree = create_file_tree(
                os.path.join(directory, item), 
                new_prefix, 
                show_files, 
                max_depth, 
                current_depth + 1
            )
            tree += sub_tree
        
        # Process files
        if show_files:
            for i, item in enumerate(files):
                is_last = (i == len(files) - 1)
                tree += f"{prefix}{'└── ' if is_last else '├── '}{item}\n"
                
    except PermissionError:
        tree += f"{prefix}[Permission Denied]\n"
    except Exception as e:
        tree += f"{prefix}[Error: {str(e)}]\n"
    
    return tree

def save_tree_to_file(tree, output_file):
    """Saves the tree representation to a file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(tree)

def main():
    parser = argparse.ArgumentParser(
        description="Generate a tree view of folder structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python file_tree.py /path/to/folder           # Show tree for a folder
  python file_tree.py .                         # Show tree for current directory
  python file_tree.py /path -d 2                # Limit depth to 2 levels
  python file_tree.py /path --dirs-only         # Show only directories
  python file_tree.py /path -o tree.txt         # Save output to file
        """
    )
    
    parser.add_argument(
        "directory", 
        nargs="?", 
        default=".",
        help="Directory to analyze (default: current directory)"
    )
    parser.add_argument(
        "-d", "--depth", 
        type=int, 
        default=None,
        help="Maximum depth to traverse"
    )
    parser.add_argument(
        "--dirs-only", 
        action="store_true",
        help="Show only directories (exclude files)"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str,
        help="Save output to file"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    target_dir = os.path.abspath(args.directory)
    if not os.path.exists(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist!")
        return
    
    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a directory!")
        return
    
    # Generate tree
    print(f"Generating tree for: {target_dir}")
    print("=" * 50)
    
    root_name = os.path.basename(target_dir) or target_dir
    tree = f"{root_name}/\n"
    
    # Get all items at root level
    try:
        items = sorted(os.listdir(target_dir))
        dirs = [item for item in items if os.path.isdir(os.path.join(target_dir, item))]
        files = [item for item in items if os.path.isfile(os.path.join(target_dir, item))]
        
        # Process directories
        for i, item in enumerate(dirs):
            is_last = (i == len(dirs) - 1) and (not args.dirs_only or not files)
            tree += f"{'└── ' if is_last else '├── '}{item}/\n"
            new_prefix = "    " if is_last else "│   "
            sub_tree = create_file_tree(
                os.path.join(target_dir, item),
                new_prefix,
                not args.dirs_only,
                args.depth,
                1
            )
            tree += sub_tree
        
        # Process files
        if not args.dirs_only:
            for i, item in enumerate(files):
                is_last = (i == len(files) - 1)
                tree += f"{'└── ' if is_last else '├── '}{item}\n"
                
    except Exception as e:
        print(f"Error reading directory: {e}")
        return
    
    # Output the tree
    print(tree)
    
    # Save to file if requested
    if args.output:
        save_tree_to_file(tree, args.output)
        print(f"\nTree saved to: {args.output}")

class FolderTreeVisualizer:
    """Alternative class-based approach with more features"""
    
    def __init__(self, root_path, ignore_hidden=True, max_depth=None):
        self.root_path = Path(root_path).resolve()
        self.ignore_hidden = ignore_hidden
        self.max_depth = max_depth
        self.tree_structure = []
    
    def should_ignore(self, path):
        """Check if path should be ignored"""
        if self.ignore_hidden:
            return path.name.startswith('.')
        return False
    
    def generate(self, current_path=None, depth=0, prefix=""):
        """Generate the tree structure"""
        if current_path is None:
            current_path = self.root_path
            self.tree_structure.append(f"{current_path.name}/")
        
        if self.max_depth is not None and depth >= self.max_depth:
            return
        
        try:
            items = list(current_path.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            # Filter items
            items = [item for item in items if not self.should_ignore(item)]
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "    " if is_last else "│   "
                
                if item.is_dir():
                    self.tree_structure.append(
                        f"{prefix}{'└── ' if is_last else '├── '}{item.name}/"
                    )
                    self.generate(item, depth + 1, prefix + current_prefix)
                else:
                    self.tree_structure.append(
                        f"{prefix}{'└── ' if is_last else '├── '}{item.name}"
                    )
        except PermissionError:
            self.tree_structure.append(f"{prefix}[Permission Denied]")
    
    def display(self):
        """Print the tree structure"""
        print("\n".join(self.tree_structure))
    
    def save_to_file(self, filename):
        """Save tree structure to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.tree_structure))

# Quick usage examples
if __name__ == "__main__":
    # Method 1: Using command line arguments
    main()
    
    # Method 2: Using the class directly (uncomment to use)
    """
    # Create a tree visualizer for current directory
    visualizer = FolderTreeVisualizer(".", ignore_hidden=True, max_depth=3)
    visualizer.generate()
    visualizer.display()
    visualizer.save_to_file("folder_structure.txt")
    """