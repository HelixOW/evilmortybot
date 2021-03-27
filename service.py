import main as production
import beta
import sys

if __name__ == '__main__':
    if len(sys.argv) == 1:
        production.start_up_bot()

    if sys.argv[1] == "prod":
        production.start_up_bot()
    else:
        beta.start_up_bot(token_path="data/beta_token.txt", _is_beta=True)
